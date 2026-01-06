"""
RAG-based Natural Language to SQL Generator (Pattern II)
스키마 메타데이터와 참조 데이터를 활용한 Text-to-SQL 시스템
"""

import os
import pandas as pd
import google.generativeai as genai
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import re

from config.config_loader import get_config
from core.schema_loader import SchemaLoader
from prompts.loader import PromptLoader
from utils.logger import setup_logger, log_nl2sql_generation


@dataclass
class SQLGenerationResult:
    """SQL 생성 결과"""
    success: bool
    sql_query: str
    analysis: Dict
    error_message: Optional[str] = None
    referenced_tables: List[str] = None
    relevant_examples: List[str] = None


class NL2SQLGenerator:
    """RAG 기반 자연어 → SQL 변환기"""

    def __init__(self, enable_logging: bool = True):
        """초기화"""
        self.gemini_model = self._initialize_gemini()

        # === RAG Enhancement: Unified SchemaLoader ===
        self.schema_loader = SchemaLoader()
        self.reference_data = self._load_reference_data()

        # === Prompt Optimization: PromptLoader ===
        self.prompt_loader = PromptLoader()

        # 예시 SQL 쿼리 (Few-shot learning용)
        self.example_queries = self._load_example_queries()

        # === Logging ===
        self.logger = setup_logger("nl2sql_generator") if enable_logging else None

        print(f"✅ NL2SQL Generator 초기화 완료 (RAG Enhanced + Prompt Optimized)")
        print(f"  - Schema: databricks_schema_for_rag.csv (unified)")
        print(f"  - 참조 데이터: {len(self.reference_data)} categories")
        print(f"  - 예시 쿼리: {len(self.example_queries)}개")
        print(f"  - Prompt: External templates (optimized)")
        print(f"  - Logging: {'Enabled' if enable_logging else 'Disabled'}")

    def _initialize_gemini(self):
        """Gemini API 초기화 (centralized config)"""
        config = get_config()
        api_key = config.get_gemini_api_key()

        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.0-flash-exp')

    # Removed: _load_notion_columns() - now using SchemaLoader

    def _load_reference_data(self) -> Dict[str, pd.DataFrame]:
        """참조 데이터 로드 (전체 로드 - RAG 용)"""
        reference_dir = "reference_data"
        ref_data = {}

        files = {
            'diseases': 'unique_diseases.csv',
            'drugs': 'unique_drugs.csv',
            'ingredients': 'unique_ingredients.csv',
        }

        for key, filename in files.items():
            filepath = os.path.join(reference_dir, filename)
            if os.path.exists(filepath):
                # RAG 개선: 전체 데이터 로드 (질병 코드 매핑용)
                df = pd.read_csv(filepath)
                ref_data[key] = df

        return ref_data

    def _load_example_queries(self) -> List[Dict]:
        """Few-shot learning을 위한 예시 쿼리"""
        return [
            {
                "question": "고혈압 환자의 남녀 성별 분포를 알려주세요",
                "sql": """SELECT
    ip.gender AS `성별`,
    COUNT(DISTINCT bt.user_id) AS `환자수`
FROM basic_treatment bt
JOIN insured_person ip ON bt.user_id = ip.user_id
WHERE bt.deleted = FALSE
    AND bt.res_disease_code LIKE 'AI1%'
GROUP BY ip.gender
ORDER BY `환자수` DESC""",
                "tables": ["basic_treatment", "insured_person"]
            },
            {
                "question": "당뇨병 환자에게 가장 많이 처방된 약물 TOP 5",
                "sql": """SELECT
    pd.res_drug_name AS `약물명`,
    COUNT(*) AS `처방횟수`
FROM basic_treatment bt
JOIN prescribed_drug pd
    ON bt.user_id = pd.user_id
    AND bt.res_treat_start_date = pd.res_treat_start_date
WHERE bt.deleted = FALSE
    AND pd.deleted = FALSE
    AND bt.res_disease_code LIKE 'AE1%'
GROUP BY pd.res_drug_name
ORDER BY `처방횟수` DESC
LIMIT 5""",
                "tables": ["basic_treatment", "prescribed_drug"]
            },
            {
                "question": "서울 지역 병원에서 치료받은 암 환자 수",
                "sql": """SELECT
    COUNT(DISTINCT user_id) AS `환자수`
FROM basic_treatment
WHERE deleted = FALSE
    AND res_disease_code LIKE 'AC%'
    AND res_hospital_name LIKE '%서울%'""",
                "tables": ["basic_treatment"]
            },
            {
                "question": "최근 1년간 조현병으로 치료받은 환자 수",
                "sql": """SELECT
    COUNT(DISTINCT user_id) AS `환자수`
FROM basic_treatment
WHERE deleted = FALSE
    AND res_disease_code LIKE 'AF2%'
    AND TRY_TO_DATE(res_treat_start_date, 'yyyyMMdd') >= DATE_SUB(CURRENT_DATE, 365)""",
                "tables": ["basic_treatment"]
            },
            {
                "question": "20대 여성 비만 환자에게 가장 많이 처방된 약물 TOP 10",
                "sql": """SELECT
    pd.res_drug_name AS `약물명`,
    COUNT(*) AS `처방횟수`
FROM basic_treatment bt
JOIN insured_person ip ON bt.user_id = ip.user_id
JOIN prescribed_drug pd ON bt.user_id = pd.user_id AND bt.res_treat_start_date = pd.res_treat_start_date
WHERE bt.deleted = FALSE
    AND pd.deleted = FALSE
    AND ip.gender = 'WOMAN'
    AND YEAR(CURRENT_DATE) - YEAR(TRY_TO_DATE(ip.birthday, 'yyyyMMdd')) BETWEEN 20 AND 29
    AND bt.res_disease_code LIKE 'AE66%'
GROUP BY pd.res_drug_name
ORDER BY `처방횟수` DESC
LIMIT 10""",
                "tables": ["basic_treatment", "insured_person", "prescribed_drug"]
            },
            {
                "question": "서울 지역 65세 이상 환자의 평균 처방 약품 수",
                "sql": """-- 서울 지역 65세 이상 환자의 평균 처방 약품 수
SELECT
    AVG(drug_count) AS `평균 처방 약품 수`
FROM (
    SELECT
        bt.user_id,
        COUNT(DISTINCT pd.res_drug_name) AS drug_count
    FROM basic_treatment bt
    JOIN insured_person ip ON bt.user_id = ip.user_id
    LEFT JOIN prescribed_drug pd
        ON bt.user_id = pd.user_id
        AND bt.res_treat_start_date = pd.res_treat_start_date
    WHERE bt.res_hospital_name LIKE '%서울%'
        AND YEAR(CURRENT_DATE) - YEAR(TRY_TO_DATE(ip.birthday, 'yyyyMMdd')) >= 65
        AND bt.deleted = FALSE
        AND pd.deleted = FALSE
    GROUP BY bt.user_id
) AS subquery""",
                "tables": ["basic_treatment", "insured_person", "prescribed_drug"]
            },
            {
                "question": "각 질병별로 환자 수 순위를 매겨줘 (RANK 사용)",
                "sql": """-- 질병별 환자 수 순위
SELECT
    res_disease_name AS `질병명`,
    patient_count AS `환자수`,
    RANK() OVER (ORDER BY patient_count DESC) AS `순위`
FROM (
    SELECT
        res_disease_name,
        COUNT(DISTINCT user_id) AS patient_count
    FROM basic_treatment
    WHERE deleted = FALSE
    GROUP BY res_disease_name
) AS disease_counts
ORDER BY `순위`
LIMIT 100""",
                "tables": ["basic_treatment"]
            },
            {
                "question": "연령대별 환자 수를 계산하고 누적 합계도 표시해줘",
                "sql": """-- 연령대별 환자 수 및 누적 합계
WITH AgeGroupCounts AS (
    SELECT
        CASE
            WHEN YEAR(CURRENT_DATE) - YEAR(TRY_TO_DATE(ip.birthday, 'yyyyMMdd')) < 30 THEN '20대 이하'
            WHEN YEAR(CURRENT_DATE) - YEAR(TRY_TO_DATE(ip.birthday, 'yyyyMMdd')) < 40 THEN '30대'
            WHEN YEAR(CURRENT_DATE) - YEAR(TRY_TO_DATE(ip.birthday, 'yyyyMMdd')) < 50 THEN '40대'
            WHEN YEAR(CURRENT_DATE) - YEAR(TRY_TO_DATE(ip.birthday, 'yyyyMMdd')) < 60 THEN '50대'
            ELSE '60대 이상'
        END AS age_group,
        COUNT(DISTINCT bt.user_id) AS patient_count
    FROM basic_treatment bt
    JOIN insured_person ip ON bt.user_id = ip.user_id
    WHERE bt.deleted = FALSE
        AND TRY_TO_DATE(ip.birthday, 'yyyyMMdd') IS NOT NULL
    GROUP BY age_group
)
SELECT
    age_group AS `연령대`,
    patient_count AS `환자수`,
    SUM(patient_count) OVER (
        ORDER BY CASE
            WHEN age_group = '20대 이하' THEN 1
            WHEN age_group = '30대' THEN 2
            WHEN age_group = '40대' THEN 3
            WHEN age_group = '50대' THEN 4
            ELSE 5
        END
    ) AS `누적 합계`
FROM AgeGroupCounts
ORDER BY
    CASE
        WHEN age_group = '20대 이하' THEN 1
        WHEN age_group = '30대' THEN 2
        WHEN age_group = '40대' THEN 3
        WHEN age_group = '50대' THEN 4
        ELSE 5
    END""",
                "tables": ["basic_treatment", "insured_person"]
            },
            {
                "question": "성별, 연령대별 환자 수를 교차 집계해줘",
                "sql": """-- 성별 × 연령대 교차 집계
SELECT
    ip.gender AS `성별`,
    CASE
        WHEN YEAR(CURRENT_DATE) - YEAR(TRY_TO_DATE(ip.birthday, 'yyyyMMdd')) < 30 THEN '20대 이하'
        WHEN YEAR(CURRENT_DATE) - YEAR(TRY_TO_DATE(ip.birthday, 'yyyyMMdd')) < 40 THEN '30대'
        WHEN YEAR(CURRENT_DATE) - YEAR(TRY_TO_DATE(ip.birthday, 'yyyyMMdd')) < 50 THEN '40대'
        WHEN YEAR(CURRENT_DATE) - YEAR(TRY_TO_DATE(ip.birthday, 'yyyyMMdd')) < 60 THEN '50대'
        ELSE '60대 이상'
    END AS `연령대`,
    COUNT(DISTINCT bt.user_id) AS `환자수`
FROM basic_treatment bt
JOIN insured_person ip ON bt.user_id = ip.user_id
WHERE bt.deleted = FALSE
    AND TRY_TO_DATE(ip.birthday, 'yyyyMMdd') IS NOT NULL
GROUP BY ip.gender, `연령대`
ORDER BY ip.gender, `연령대`""",
                "tables": ["basic_treatment", "insured_person"]
            },
            {
                "question": "2023년 1월부터 12월까지 진료받은 환자 수는?",
                "sql": """-- 특정 기간 환자 수 (BETWEEN 사용)
SELECT
    COUNT(DISTINCT user_id) AS `환자수`
FROM basic_treatment
WHERE deleted = FALSE
    AND TRY_TO_DATE(res_treat_start_date, 'yyyyMMdd')
        BETWEEN TRY_TO_DATE('20230101', 'yyyyMMdd')
        AND TRY_TO_DATE('20231231', 'yyyyMMdd')""",
                "tables": ["basic_treatment"]
            }
        ]

    def _extract_keywords(self, query: str) -> List[str]:
        """사용자 쿼리에서 키워드 추출"""
        # 일반 키워드
        keywords = ['환자', '처방', '약물', '병원', '지역', '성별', '연령', '남성', '여성',
                   '분포', '비율', '수', '개수', 'TOP', '상위', '많이', '적게']
        medical_keywords = [kw for kw in keywords if kw in query]

        return medical_keywords

    def _find_disease_codes(self, query: str) -> List[Dict[str, str]]:
        """
        RAG: 쿼리에서 질병명을 찾아 해당하는 질병 코드 반환

        Returns:
            List[Dict]: [{'disease_name': '고혈압', 'disease_code': 'AI109', 'pattern': 'AI1%'}, ...]
        """
        disease_matches = []
        diseases_df = self.reference_data.get('diseases', pd.DataFrame())

        if diseases_df.empty:
            return disease_matches

        # 주요 질병 키워드 매핑 (부분 매칭용)
        disease_keywords = {
            '고혈압': ['고혈압'],
            '당뇨': ['당뇨', '당뇨병'],
            '암': ['암'],
            '위염': ['위염'],
            '감기': ['감기', '독감'],
            '조현병': ['조현병'],
            '비만': ['비만'],
            '폐렴': ['폐렴'],
            '천식': ['천식'],
            '우울': ['우울증', '우울'],
            '치매': ['치매', '알츠하이머'],
            '파킨슨': ['파킨슨'],
            '간염': ['간염', '간경화'],
            '신부전': ['신부전'],
            '심부전': ['심부전'],
        }

        # 쿼리에서 질병 키워드 감지
        for disease_key, keywords in disease_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    # 해당 질병명이 포함된 질병 코드 찾기
                    matching_diseases = diseases_df[
                        diseases_df['name'].str.contains(keyword, na=False, case=False)
                    ].head(3)  # 상위 3개만

                    for _, row in matching_diseases.iterrows():
                        code = row['code']
                        if code and code != '$':
                            # 코드 패턴 생성 (예: AI109 → AI1%)
                            pattern = code[:3] + '%' if len(code) >= 3 else code + '%'
                            disease_matches.append({
                                'disease_name': row['name'],
                                'disease_code': code,
                                'pattern': pattern,
                                'keyword': keyword
                            })
                    break  # 첫 번째 매칭 키워드만 사용

        return disease_matches

    # Removed: _search_relevant_schema() - now delegating to SchemaLoader

    # Removed: _create_schema_context() - now using SchemaLoader.format_schema_for_llm()

    def _select_relevant_examples(self, query: str, keywords: List[str]) -> List[Dict]:
        """쿼리와 유사한 예시 선택 (개선: 패턴 매칭 강화)"""
        query_lower = query.lower()

        # 쿼리 패턴 감지
        patterns = {
            'rank': 'rank' in query_lower or '순위' in query_lower or 'top' in query_lower.replace('top ', ''),
            'window_func': any(kw in query_lower for kw in ['순위', '누적', '비율', '합계', 'rank', 'row_number']),
            'aggregation': any(kw in query_lower for kw in ['교차', '집계', '분포', '그룹', 'group']),
            'join': any(kw in query_lower for kw in ['성별', '연령', '약', '처방', 'gender', 'age']),
            'date_range': any(kw in query_lower for kw in ['년', '월', '일', '기간', '이후', '이전', '동안']),
            'age_filter': any(kw in query_lower for kw in ['세', '연령', 'age']),
            'location': any(kw in query_lower for kw in ['지역', '서울', '부산', '병원명'])
        }

        scored_examples = []

        for example in self.example_queries:
            ex_lower = example['question'].lower()
            score = 0

            # 패턴 매칭 점수 (가중치 높음)
            if patterns['rank'] and 'rank' in ex_lower:
                score += 10
            if patterns['window_func'] and any(kw in ex_lower for kw in ['순위', '누적', '비율']):
                score += 8
            if patterns['aggregation'] and any(kw in ex_lower for kw in ['교차', '집계', '분포']):
                score += 8
            if patterns['age_filter'] and ('세' in ex_lower or 'age' in ex_lower):
                score += 7
            if patterns['location'] and any(kw in ex_lower for kw in ['지역', '서울', '병원']):
                score += 7
            if patterns['date_range'] and any(kw in ex_lower for kw in ['년', '기간', '이후']):
                score += 6

            # 키워드 매칭 점수
            keyword_matches = sum(1 for kw in keywords if kw in ex_lower)
            score += keyword_matches * 2

            # 테이블 복잡도 매칭 (JOIN 여부)
            if patterns['join'] and len(example['tables']) > 1:
                score += 5

            if score > 0:
                scored_examples.append((score, example))

        # 점수 순으로 정렬하여 상위 3개 반환 (2개 → 3개로 증가)
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [ex for score, ex in scored_examples[:3]]

    def _create_llm_prompt(self, query: str, schema_context: str, examples: List[Dict], disease_hints: str = "") -> str:
        """LLM 프롬프트 생성 (PromptLoader 사용 + 질병 코드 힌트)"""
        base_prompt = self.prompt_loader.load_nl2sql_prompt(
            user_query=query,
            schema_context=schema_context,
            relevant_examples=examples
        )

        # RAG 개선: 질병 코드 힌트 추가
        if disease_hints:
            base_prompt += f"\n\n## 🎯 질병 코드 힌트 (RAG 자동 검색 결과)\n\n{disease_hints}"

        return base_prompt

    def generate_sql(self, user_query: str) -> SQLGenerationResult:
        """
        자연어 → SQL 변환 (RAG Pattern)

        Args:
            user_query: 사용자 자연어 요청

        Returns:
            SQLGenerationResult
        """
        try:
            # 1. 키워드 추출
            keywords = self._extract_keywords(user_query)
            print(f"📌 추출된 키워드: {keywords}")

            # 2. === RAG Enhancement: 질병 코드 자동 검색 ===
            disease_codes = self._find_disease_codes(user_query)
            disease_hints = ""
            if disease_codes:
                print(f"🔍 RAG 질병 코드 발견: {len(disease_codes)}개")
                hints = []
                for dc in disease_codes[:3]:  # 최대 3개만
                    hints.append(
                        f"- '{dc['keyword']}' → `res_disease_code LIKE '{dc['pattern']}'` "
                        f"(예: {dc['disease_name']} 코드: {dc['disease_code']})"
                    )
                disease_hints = "\n".join(hints)
                disease_hints += "\n\n**중요**: 위 질병 코드를 반드시 사용하세요!"
                print(f"💡 질병 코드 힌트:\n{disease_hints}")

            # 3. === RAG Enhancement: Use unified SchemaLoader ===
            relevant_schema = self.schema_loader.get_relevant_schema(
                query=user_query,
                top_k=30,
                include_core_tables=True
            )
            print(f"📊 관련 테이블: {relevant_schema['테이블명'].unique().tolist()}")
            print(f"📊 스키마 컬럼 수: {len(relevant_schema)}")

            # 4. 스키마 컨텍스트 생성 (unified formatter)
            schema_context = self.schema_loader.format_schema_for_llm(relevant_schema)

            # 5. 유사 예시 선택 (Few-shot)
            examples = self._select_relevant_examples(user_query, keywords)
            print(f"📚 선택된 예시: {len(examples)}개")

            # 6. LLM 프롬프트 생성 (질병 코드 힌트 포함)
            prompt = self._create_llm_prompt(user_query, schema_context, examples, disease_hints)

            # 7. Gemini API 호출
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text.strip()

            # 8. JSON 파싱
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            result = json.loads(response_text)

            # 로깅
            if self.logger:
                log_nl2sql_generation(
                    self.logger,
                    user_query=user_query,
                    success=True,
                    rag_detected=bool(disease_codes),
                    disease_codes=[dc['pattern'] for dc in disease_codes] if disease_codes else []
                )

            return SQLGenerationResult(
                success=True,
                sql_query=result.get('sql', ''),
                analysis=result.get('analysis', {}),
                referenced_tables=result.get('analysis', {}).get('required_tables', []),
                relevant_examples=[ex['question'] for ex in examples]
            )

        except json.JSONDecodeError as e:
            error_msg = f"JSON 파싱 실패: LLM 응답 형식이 올바르지 않습니다. {str(e)}"
            if self.logger:
                log_nl2sql_generation(self.logger, user_query, success=False, error=error_msg)
            return SQLGenerationResult(
                success=False,
                sql_query='',
                analysis={},
                error_message=error_msg
            )
        except KeyError as e:
            error_msg = f"응답 구조 오류: 필수 키({str(e)})가 누락되었습니다."
            if self.logger:
                log_nl2sql_generation(self.logger, user_query, success=False, error=error_msg)
            return SQLGenerationResult(
                success=False,
                sql_query='',
                analysis={},
                error_message=error_msg
            )
        except Exception as e:
            # 상세한 에러 정보 제공
            error_type = type(e).__name__
            error_msg = f"SQL 생성 실패 ({error_type}): {str(e)}"
            if self.logger:
                log_nl2sql_generation(self.logger, user_query, success=False, error=error_msg)
            return SQLGenerationResult(
                success=False,
                sql_query='',
                analysis={},
                error_message=error_msg
            )

    def refine_sql(
        self,
        original_query: str,
        current_sql: str,
        refinement_request: str
    ) -> SQLGenerationResult:
        """
        기존 SQL을 사용자 피드백에 따라 개선

        Args:
            original_query: 원래 자연어 요청
            current_sql: 현재 생성된 SQL
            refinement_request: 사용자의 개선 요청 (예: "서울 지역만 필터링해주세요")

        Returns:
            SQLGenerationResult: 개선된 SQL 결과
        """
        try:
            print(f"\n🔄 SQL 개선 시작...")
            print(f"  - 원래 요청: {original_query}")
            print(f"  - 개선 요청: {refinement_request}")

            # 1. 개선 요청에서 키워드 추출
            keywords = self._extract_keywords(refinement_request)
            print(f"  - 추출된 키워드: {keywords}")

            # 2. 질병 코드 검색 (개선 요청에서)
            disease_codes = self._find_disease_codes(refinement_request)
            disease_hints = ""
            if disease_codes:
                print(f"  - 🎯 RAG 질병 코드 발견: {len(disease_codes)}개")
                disease_hints = self._format_disease_hints(disease_codes)

            # 3. 관련 스키마 추출 (원래 요청 + 개선 요청 결합)
            combined_query = original_query + " " + refinement_request
            schema_context = self.schema_loader.get_relevant_schema(combined_query, top_k=15)
            print(f"  - 스키마: {len(schema_context)} rows")

            # 4. 개선 프롬프트 생성
            prompt = self._create_refinement_prompt(
                original_query=original_query,
                current_sql=current_sql,
                refinement_request=refinement_request,
                schema_context=schema_context,
                disease_hints=disease_hints
            )

            # 5. Gemini API 호출
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text.strip()

            # 6. JSON 파싱
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            result = json.loads(response_text)

            # 로깅
            if self.logger:
                log_nl2sql_generation(
                    self.logger,
                    user_query=f"[개선] {refinement_request}",
                    success=True,
                    rag_detected=bool(disease_codes),
                    disease_codes=[dc['pattern'] for dc in disease_codes] if disease_codes else []
                )

            print(f"✅ SQL 개선 완료")

            return SQLGenerationResult(
                success=True,
                sql_query=result.get('sql', ''),
                analysis=result.get('analysis', {}),
                referenced_tables=result.get('analysis', {}).get('required_tables', [])
            )

        except Exception as e:
            error_type = type(e).__name__
            error_msg = f"SQL 개선 실패 ({error_type}): {str(e)}"
            if self.logger:
                log_nl2sql_generation(self.logger, f"[개선] {refinement_request}", success=False, error=error_msg)
            return SQLGenerationResult(
                success=False,
                sql_query='',
                analysis={},
                error_message=error_msg
            )

    def _create_refinement_prompt(
        self,
        original_query: str,
        current_sql: str,
        refinement_request: str,
        schema_context: pd.DataFrame,
        disease_hints: str
    ) -> str:
        """SQL 개선용 프롬프트 생성"""
        # System prompt
        from pathlib import Path
        system_prompt_path = Path("prompts") / "nl2sql" / "system.txt"
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()

        # Schema context
        schema_text = self.schema_loader.format_schema_for_llm(schema_context)

        # 예시 쿼리 (간단하게 2개만)
        examples = self.example_queries[:2]
        examples_text = "\n\n".join([
            f"**예시 {i+1}:**\n질문: {ex['question']}\nSQL:\n```sql\n{ex['sql']}\n```"
            for i, ex in enumerate(examples)
        ])

        refinement_prompt = f"""
{system_prompt}

---

### 📊 스키마 정보
{schema_text}

### 💡 Few-shot 예시
{examples_text}

---

## 🔄 SQL 개선 요청

**원래 요청:**
{original_query}

**현재 생성된 SQL:**
```sql
{current_sql}
```

**사용자 개선 요청:**
{refinement_request}

{disease_hints}

---

## 🎯 개선 지침

1. **현재 SQL을 기반**으로 사용자의 개선 요청을 반영하세요
2. **기존 로직은 유지**하되, 요청된 변경 사항만 적용하세요
3. **질병 코드 힌트**가 제공된 경우 반드시 활용하세요
4. **전체 SQL을 다시 생성**하세요 (부분 수정이 아님)

응답 형식 (JSON):
```json
{{
  "sql": "개선된 전체 SQL 쿼리 (Spark SQL)",
  "analysis": {{
    "required_tables": ["테이블1", "테이블2"],
    "key_conditions": ["조건1", "조건2"],
    "explanation": "개선 내용 설명"
  }}
}}
```
"""
        return refinement_prompt


if __name__ == "__main__":
    # 테스트
    generator = NL2SQLGenerator()

    test_queries = [
        "고혈압 환자의 성별 분포를 보여주세요",
        "당뇨병 환자에게 가장 많이 처방된 약물 TOP 10을 알려주세요",
        "서울 지역 3차 병원에서 치료받은 암 환자는 몇 명인가요?",
    ]

    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"🔍 Query: {query}")
        print(f"{'='*70}")

        result = generator.generate_sql(query)

        if result.success:
            print(f"\n📊 분석:")
            for key, value in result.analysis.items():
                print(f"  - {key}: {value}")

            print(f"\n💡 참고 예시: {result.relevant_examples}")
            print(f"\n📝 생성된 SQL:")
            print(result.sql_query)
        else:
            print(f"\n❌ 오류: {result.error_message}")
