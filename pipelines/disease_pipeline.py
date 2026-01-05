"""
Disease-Centric Pipeline Analysis System - Phase 6
질환 중심 파이프라인 분석 시스템
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import google.generativeai as genai

from core.recipe_loader import RecipeLoader
from core.sql_template_engine import SQLTemplateEngine
from core.schema_loader import SchemaLoader
from config.config_loader import get_config
from prompts.loader import PromptLoader


@dataclass
class PipelineResult:
    """파이프라인 분석 결과"""
    disease_name: str
    core_recipes: List[Dict[str, Any]]  # 4개 고정 레시피 결과
    recommended_recipes: List[str]  # LLM 추천 레시피 이름들
    approved_recipes: List[str]  # 사용자 승인된 레시피 이름들
    executed_results: List[Dict[str, Any]]  # 실행된 모든 레시피 결과
    success_rate: float


class DiseaseAnalysisPipeline:
    """질환 중심 파이프라인 분석 엔진"""

    # 4개 고정 코어 레시피
    CORE_RECIPES = [
        "get_patient_count_by_disease_keyword",
        "get_demographic_distribution_by_disease",
        "analyze_screened_regional_distribution",
        "get_top_prescribed_ingredients_by_disease"
    ]

    def __init__(self, recipe_dir: str = "recipes"):
        """
        Args:
            recipe_dir: 레시피 디렉토리 경로
        """
        self.recipe_loader = RecipeLoader(recipe_dir)
        self.sql_engine = SQLTemplateEngine(recipe_dir)
        self.schema_loader = SchemaLoader()  # RAG 추가
        self.prompt_loader = PromptLoader()  # Prompt Optimization

        # Gemini API 초기화 (centralized config)
        config = get_config()
        api_key = config.get_gemini_api_key()

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

        print("✅ DiseaseAnalysisPipeline initialized (Prompt Optimized)")
        print(f"   - Loaded {len(self.recipe_loader.all_recipes)} recipes")
        print(f"   - Schema loader: {len(self.schema_loader.schema_df)} columns")
        print(f"   - Core recipes: {len(self.CORE_RECIPES)}")
        print(f"   - Prompt: External templates (optimized)")

    def execute_core_recipes(self, disease_name: str) -> List[Dict[str, Any]]:
        """
        4개 고정 코어 레시피 실행

        Args:
            disease_name: 질환명 (예: "당뇨병", "고혈압")

        Returns:
            실행 결과 리스트 (각 레시피별 결과)
        """
        results = []

        for recipe_name in self.CORE_RECIPES:
            try:
                # 레시피 메타데이터 로드
                recipe = self.recipe_loader.get_recipe_by_name(recipe_name)
                if not recipe:
                    results.append({
                        'recipe_name': recipe_name,
                        'success': False,
                        'error': f'Recipe {recipe_name} not found'
                    })
                    continue

                # 파라미터 자동 설정 - 모든 파라미터에 값 할당
                from datetime import datetime, timedelta
                parameters = {}

                for param in recipe.get('parameters', []):
                    param_name = param['name']
                    param_type = param.get('type', 'string')

                    # 질환명 파라미터
                    if 'disease' in param_name.lower() or 'keyword' in param_name.lower():
                        parameters[param_name] = disease_name

                    # 날짜 파라미터 - 최근 3년
                    elif param_type == 'date':
                        if 'start' in param_name.lower():
                            parameters[param_name] = (datetime.now() - timedelta(days=1095)).strftime('%Y-%m-%d')
                        elif 'end' in param_name.lower():
                            parameters[param_name] = datetime.now().strftime('%Y-%m-%d')
                        else:
                            parameters[param_name] = datetime.now().strftime('%Y-%m-%d')

                    # 정수 파라미터 - 반드시 기본값 설정
                    elif param_type == 'integer':
                        default_value = param.get('default')
                        if default_value is not None:
                            parameters[param_name] = default_value
                        else:
                            parameters[param_name] = 365

                    # 성분 파라미터
                    elif 'ingredient' in param_name.lower():
                        parameters[param_name] = ''

                    # 기타 문자열 파라미터 - 빈 문자열로 초기화
                    elif param_type == 'string' and param_name not in parameters:
                        parameters[param_name] = ''

                # SQL 생성
                sql_query = self.sql_engine.render_template(recipe_name, parameters)

                results.append({
                    'recipe_name': recipe_name,
                    'success': True,
                    'sql_query': sql_query,
                    'parameters': parameters,
                    'metadata': recipe
                })

            except Exception as e:
                results.append({
                    'recipe_name': recipe_name,
                    'success': False,
                    'error': str(e)
                })

        return results

    def recommend_additional_recipes(
        self,
        disease_name: str,
        target_count: int = 7
    ) -> List[str]:
        """
        LLM을 사용하여 질환에 맞는 추가 레시피 추천

        Args:
            disease_name: 질환명
            target_count: 추천할 레시피 개수 (기본 7개)

        Returns:
            추천 레시피 이름 리스트
        """
        # 코어 레시피 제외한 모든 레시피 목록
        available_recipes = [
            recipe for recipe in self.recipe_loader.all_recipes
            if recipe['name'] not in self.CORE_RECIPES
        ]

        # === RAG Enhancement: 스키마 정보 추가 ===
        query = f"{disease_name} 질환 환자 분석"
        relevant_schema = self.schema_loader.get_relevant_schema(query, top_k=20)
        schema_info = self.schema_loader.format_schema_for_llm(relevant_schema)

        # LLM 프롬프트 구성
        recipe_descriptions = "\n".join([
            f"- {r['name']}: {r['description']}"
            for r in available_recipes
        ])

        # === Prompt Optimization: PromptLoader 사용 ===
        prompt = self.prompt_loader.load_recipe_recommendation_prompt(
            disease_name=disease_name,
            recipe_list=recipe_descriptions,
            schema_info=schema_info,
            target_count=target_count
        )

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # JSON 파싱
            import json
            # Markdown 코드 블록 제거
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            result = json.loads(response_text)
            recommended = result.get('recommended_recipes', [])

            # 유효성 검증
            available_names = [r['name'] for r in available_recipes]
            validated_recommendations = [
                name for name in recommended
                if name in available_names
            ]

            print(f"✅ LLM recommended {len(validated_recommendations)} recipes")
            if len(validated_recommendations) < target_count:
                print(f"⚠️ Warning: Only {len(validated_recommendations)}/{target_count} recommendations were valid")

            return validated_recommendations[:target_count]

        except Exception as e:
            print(f"❌ LLM recommendation failed: {e}")
            # Fallback: 랜덤하게 선택
            import random
            fallback = random.sample(
                [r['name'] for r in available_recipes],
                min(target_count, len(available_recipes))
            )
            print(f"⚠️ Using fallback selection: {len(fallback)} recipes")
            return fallback

    def refine_recommendations_with_nl(
        self,
        disease_name: str,
        current_recommendations: List[str],
        user_feedback: str
    ) -> List[str]:
        """
        자연어 피드백을 기반으로 레시피 추천 조정

        Args:
            disease_name: 질환명
            current_recommendations: 현재 추천된 레시피 이름 리스트
            user_feedback: 사용자의 자연어 피드백 (예: "비용 관련 분석 더 추가해줘")

        Returns:
            조정된 레시피 이름 리스트
        """
        # 코어 레시피 제외한 모든 레시피 목록
        available_recipes = [
            recipe for recipe in self.recipe_loader.all_recipes
            if recipe['name'] not in self.CORE_RECIPES
        ]

        recipe_descriptions = "\n".join([
            f"- {r['name']}: {r['description']}"
            for r in available_recipes
        ])

        current_list = "\n".join([f"- {name}" for name in current_recommendations])

        prompt = f"""당신은 임상 데이터 분석 전문가입니다.

질환명: {disease_name}

현재 추천된 레시피 목록:
{current_list}

사용자 피드백:
"{user_feedback}"

위 피드백을 반영하여 레시피 목록을 조정해주세요.

사용 가능한 전체 레시피:
{recipe_descriptions}

**규칙:**
1. 사용자 피드백에 따라 레시피를 추가/제거/교체하세요
2. 총 개수는 기존과 비슷하게 유지하세요 (±2개 허용)
3. 피드백에 명시적으로 요청된 내용을 최우선으로 반영하세요

응답 형식 (JSON):
{{
  "refined_recipes": [
    "recipe_name_1",
    "recipe_name_2",
    ...
  ],
  "changes": "어떤 변경을 했는지 간단히"
}}
"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # JSON 파싱
            import json
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            result = json.loads(response_text)
            refined = result.get('refined_recipes', [])

            # 유효성 검증
            available_names = [r['name'] for r in available_recipes]
            validated_refined = [
                name for name in refined
                if name in available_names
            ]

            print(f"✅ Refined recommendations: {len(validated_refined)} recipes")
            print(f"   Changes: {result.get('changes', 'N/A')}")

            return validated_refined

        except Exception as e:
            print(f"❌ Refinement failed: {e}")
            print(f"⚠️ Keeping original recommendations")
            return current_recommendations

    def execute_approved_recipes(
        self,
        disease_name: str,
        approved_recipe_names: List[str]
    ) -> List[Dict[str, Any]]:
        """
        승인된 레시피들 실행

        Args:
            disease_name: 질환명
            approved_recipe_names: 승인된 레시피 이름 리스트

        Returns:
            실행 결과 리스트
        """
        results = []

        for recipe_name in approved_recipe_names:
            try:
                recipe = self.recipe_loader.get_recipe_by_name(recipe_name)
                if not recipe:
                    results.append({
                        'recipe_name': recipe_name,
                        'success': False,
                        'error': f'Recipe {recipe_name} not found'
                    })
                    continue

                # 파라미터 자동 설정
                from datetime import datetime, timedelta
                parameters = {}

                for param in recipe.get('parameters', []):
                    param_name = param['name']
                    param_type = param.get('type', 'string')

                    # 질환명 파라미터
                    if 'disease' in param_name.lower() or 'keyword' in param_name.lower():
                        parameters[param_name] = disease_name

                    # 날짜 파라미터 - 최근 3년
                    elif param_type == 'date':
                        if 'start' in param_name.lower():
                            # 3년 전부터
                            parameters[param_name] = (datetime.now() - timedelta(days=1095)).strftime('%Y-%m-%d')
                        elif 'end' in param_name.lower():
                            # 오늘까지
                            parameters[param_name] = datetime.now().strftime('%Y-%m-%d')
                        else:
                            # 기본값 (오늘)
                            parameters[param_name] = datetime.now().strftime('%Y-%m-%d')

                    # 정수 파라미터 - 기본값 사용
                    elif param_type == 'integer':
                        parameters[param_name] = param.get('default', 365)

                    # 성분 파라미터 - 빈 문자열 (전체 성분)
                    elif 'ingredient' in param_name.lower():
                        parameters[param_name] = ''

                # SQL 생성
                sql_query = self.sql_engine.render_template(recipe_name, parameters)

                results.append({
                    'recipe_name': recipe_name,
                    'success': True,
                    'sql_query': sql_query,
                    'parameters': parameters,
                    'metadata': recipe
                })

            except Exception as e:
                results.append({
                    'recipe_name': recipe_name,
                    'success': False,
                    'error': str(e)
                })

        return results

    def run_complete_pipeline(
        self,
        disease_name: str,
        user_approved_recipes: Optional[List[str]] = None,
        natural_language_feedback: Optional[str] = None
    ) -> PipelineResult:
        """
        전체 파이프라인 실행

        Args:
            disease_name: 질환명
            user_approved_recipes: 사용자가 체크박스로 승인한 레시피 (None이면 자동 추천만 사용)
            natural_language_feedback: 사용자의 자연어 피드백 (추가 조정용)

        Returns:
            PipelineResult 객체
        """
        print(f"\n{'='*60}")
        print(f"🔬 Disease-Centric Pipeline Analysis")
        print(f"   Disease: {disease_name}")
        print(f"{'='*60}\n")

        # Step 1: 코어 레시피 실행
        print("Step 1: Executing 4 core recipes...")
        core_results = self.execute_core_recipes(disease_name)
        core_success = sum(1 for r in core_results if r.get('success', False))
        print(f"✅ Core recipes executed: {core_success}/{len(core_results)} succeeded\n")

        # Step 2: LLM 추천
        print("Step 2: LLM recommending additional recipes...")
        recommended = self.recommend_additional_recipes(disease_name, target_count=7)
        print(f"✅ Recommended {len(recommended)} recipes\n")

        # Step 3: 자연어 피드백 반영 (옵션)
        if natural_language_feedback:
            print(f"Step 3: Refining with user feedback...")
            print(f"   Feedback: '{natural_language_feedback}'")
            recommended = self.refine_recommendations_with_nl(
                disease_name,
                recommended,
                natural_language_feedback
            )
            print(f"✅ Refined to {len(recommended)} recipes\n")

        # Step 4: 사용자 승인 처리
        if user_approved_recipes is not None:
            approved = user_approved_recipes
            print(f"Step 4: User approved {len(approved)} recipes")
        else:
            # 자동 승인 (UI 없이 테스트할 때)
            approved = recommended
            print(f"Step 4: Auto-approving all {len(approved)} recommended recipes")

        # Step 5: 승인된 레시피 실행
        print(f"\nStep 5: Executing {len(approved)} approved recipes...")
        approved_results = self.execute_approved_recipes(disease_name, approved)
        approved_success = sum(1 for r in approved_results if r.get('success', False))
        print(f"✅ Approved recipes executed: {approved_success}/{len(approved_results)} succeeded\n")

        # 전체 결과 집계
        all_results = core_results + approved_results
        total_success = sum(1 for r in all_results if r.get('success', False))
        success_rate = total_success / len(all_results) if all_results else 0

        print(f"{'='*60}")
        print(f"✅ Pipeline Complete")
        print(f"   Total recipes: {len(all_results)}")
        print(f"   Success: {total_success}/{len(all_results)} ({success_rate*100:.1f}%)")
        print(f"{'='*60}\n")

        return PipelineResult(
            disease_name=disease_name,
            core_recipes=core_results,
            recommended_recipes=recommended,
            approved_recipes=approved,
            executed_results=all_results,
            success_rate=success_rate
        )
