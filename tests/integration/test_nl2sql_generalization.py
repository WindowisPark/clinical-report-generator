"""
Phase 15: NL2SQL Generalization Testing
테스트 프레임워크 with API Rate Limit Handling
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from pipelines.nl2sql_generator import NL2SQLGenerator
from services.databricks_client import DatabricksClient


class NL2SQLTester:
    """NL2SQL 테스트 자동화 프레임워크"""

    def __init__(self, batch_size: int = 5, delay_seconds: int = 10):
        """
        초기화

        Args:
            batch_size: 배치당 처리할 쿼리 수 (API rate limit 회피)
            delay_seconds: 배치 간 대기 시간 (초)
        """
        self.generator = NL2SQLGenerator()
        self.databricks = DatabricksClient()
        self.batch_size = batch_size
        self.delay_seconds = delay_seconds

        # Test cases organized by category
        self.test_cases = self._load_test_cases()

        # Results storage
        self.results = []

    def _load_test_cases(self) -> Dict[str, List[Dict[str, str]]]:
        """테스트 케이스 로드"""
        return {
            "multi_table_joins": [
                {
                    "id": "MTJ-01",
                    "query": "고혈압(AI1) 환자 중 당뇨(AE1)도 함께 있는 환자 수는?",
                    "expected_features": ["JOIN", "res_disease_code LIKE 'AI1%'", "res_disease_code LIKE 'AE1%'"]
                },
                {
                    "id": "MTJ-02",
                    "query": "서울 지역 65세 이상 환자의 평균 처방 약품 수는?",
                    "expected_features": ["JOIN", "TO_DATE(birthday", "res_city LIKE '%서울%'"]
                },
                {
                    "id": "MTJ-03",
                    "query": "최근 1년간 진료받은 환자의 질병별 분포를 알려줘",
                    "expected_features": ["JOIN", "TO_DATE(res_treat_start_date", "GROUP BY"]
                },
                {
                    "id": "MTJ-04",
                    "query": "남성 환자 중 처방받은 약물 종류가 5개 이상인 사람은?",
                    "expected_features": ["JOIN", "gender = 'M'", "COUNT", "HAVING"]
                },
                {
                    "id": "MTJ-05",
                    "query": "2020년 이후 진료받은 환자의 지역별 평균 연령은?",
                    "expected_features": ["JOIN", "TO_DATE(res_treat_start_date", "TO_DATE(birthday", "GROUP BY res_city"]
                }
            ],

            "nested_subqueries": [
                {
                    "id": "NSQ-01",
                    "query": "평균 연령보다 높은 환자만 필터링해서 질병 분포 보여줘",
                    "expected_features": ["SELECT", "FROM", "WHERE", "AVG", "TO_DATE(birthday"]
                },
                {
                    "id": "NSQ-02",
                    "query": "처방 횟수가 가장 많은 상위 10개 약물을 처방받은 환자 수는?",
                    "expected_features": ["IN", "SELECT", "ORDER BY", "LIMIT 10"]
                },
                {
                    "id": "NSQ-03",
                    "query": "서울 지역 환자 평균보다 처방 약물이 많은 환자 목록",
                    "expected_features": ["WHERE", "COUNT", "AVG", "res_city LIKE '%서울%'"]
                },
                {
                    "id": "NSQ-04",
                    "query": "최근 1년간 진료 환자 중 고혈압 환자 비율은?",
                    "expected_features": ["SELECT", "COUNT", "WHERE", "TO_DATE(res_treat_start_date"]
                },
                {
                    "id": "NSQ-05",
                    "query": "가장 많이 처방되는 약물 TOP 5를 받은 환자의 평균 연령",
                    "expected_features": ["IN", "SELECT", "ORDER BY", "LIMIT 5", "AVG", "TO_DATE(birthday"]
                }
            ],

            "window_functions": [
                {
                    "id": "WF-01",
                    "query": "각 질병별로 환자 수 순위를 매겨줘 (RANK 사용)",
                    "expected_features": ["RANK()", "OVER", "PARTITION BY", "ORDER BY"]
                },
                {
                    "id": "WF-02",
                    "query": "지역별 환자 수를 계산하고 전체 환자 대비 비율도 같이 보여줘",
                    "expected_features": ["COUNT", "SUM", "OVER()", "GROUP BY res_city"]
                },
                {
                    "id": "WF-03",
                    "query": "연령대별 환자 수를 계산하고 누적 합계도 표시해줘",
                    "expected_features": ["SUM", "OVER", "ORDER BY", "TO_DATE(birthday"]
                },
                {
                    "id": "WF-04",
                    "query": "각 약물의 처방 횟수를 계산하고 상위 10%를 표시해줘",
                    "expected_features": ["PERCENT_RANK()", "OVER", "ORDER BY", "WHERE"]
                },
                {
                    "id": "WF-05",
                    "query": "질병별 환자 수와 이전 질병 대비 증감률 계산",
                    "expected_features": ["LAG()", "OVER", "ORDER BY", "COUNT"]
                }
            ],

            "complex_aggregations": [
                {
                    "id": "CA-01",
                    "query": "성별, 연령대별 환자 수를 교차 집계해줘",
                    "expected_features": ["GROUP BY", "CASE WHEN", "TO_DATE(birthday", "gender"]
                },
                {
                    "id": "CA-02",
                    "query": "지역별로 가장 많은 질병 TOP 3을 찾아줘",
                    "expected_features": ["GROUP BY", "COUNT", "ORDER BY", "LIMIT"]
                },
                {
                    "id": "CA-03",
                    "query": "월별 신규 환자 수 추이를 보여줘 (최근 1년)",
                    "expected_features": ["DATE_FORMAT", "TO_DATE", "GROUP BY", "COUNT"]
                },
                {
                    "id": "CA-04",
                    "query": "약물별 처방 환자의 평균 연령, 중앙값, 표준편차 계산",
                    "expected_features": ["AVG", "PERCENTILE_APPROX", "STDDEV", "GROUP BY"]
                },
                {
                    "id": "CA-05",
                    "query": "질병별 남녀 비율과 평균 연령을 한 번에 보여줘",
                    "expected_features": ["GROUP BY", "COUNT", "CASE", "AVG", "TO_DATE(birthday"]
                }
            ],

            "date_range_queries": [
                {
                    "id": "DRQ-01",
                    "query": "2023년 1월부터 2023년 12월까지 진료받은 환자 수는?",
                    "expected_features": ["TO_DATE(res_treat_start_date", "BETWEEN", "2023"]
                },
                {
                    "id": "DRQ-02",
                    "query": "최근 3개월간 신규 등록된 환자의 질병 분포는?",
                    "expected_features": ["TO_DATE", ">=", "DATE_SUB", "CURRENT_DATE"]
                },
                {
                    "id": "DRQ-03",
                    "query": "1980년대 출생 환자 중 고혈압 환자 비율은?",
                    "expected_features": ["TO_DATE(birthday", "BETWEEN", "1980", "1989"]
                },
                {
                    "id": "DRQ-04",
                    "query": "각 분기별 진료 환자 수 추이를 보여줘 (2022-2023)",
                    "expected_features": ["QUARTER", "TO_DATE(res_treat_start_date", "GROUP BY"]
                },
                {
                    "id": "DRQ-05",
                    "query": "60세 이상 환자 중 최근 6개월간 진료받은 사람은?",
                    "expected_features": ["TO_DATE(birthday", "TO_DATE(res_treat_start_date", "DATE_SUB"]
                }
            ]
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """전체 테스트 실행"""
        print("=" * 80)
        print("Phase 15: NL2SQL Generalization Testing")
        print("=" * 80)
        print(f"총 테스트 케이스: {sum(len(cases) for cases in self.test_cases.values())}개")
        print(f"배치 크기: {self.batch_size}, 배치 간 대기: {self.delay_seconds}초\n")

        start_time = datetime.now()

        # Category별 테스트 실행
        for category, test_cases in self.test_cases.items():
            print(f"\n{'=' * 80}")
            print(f"Category: {category.replace('_', ' ').title()}")
            print(f"{'=' * 80}\n")

            self._run_category_tests(category, test_cases)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 결과 집계
        summary = self._calculate_summary(duration)

        # 결과 저장
        self._save_results(summary)

        # 최종 리포트 출력
        self._print_summary(summary)

        return summary

    def _run_category_tests(self, category: str, test_cases: List[Dict]):
        """카테고리별 테스트 실행 (배치 처리)"""
        for i, test_case in enumerate(test_cases, 1):
            print(f"[{test_case['id']}] Testing: {test_case['query']}")

            result = self._test_single_query(test_case, category)
            self.results.append(result)

            # 상태 표시
            status_icon = "✅" if result['sql_generated'] else "❌"
            exec_icon = "✅" if result['execution_success'] else "❌" if result['executed'] else "⏭️"
            print(f"  {status_icon} SQL 생성 | {exec_icon} 실행\n")

            # 배치 간 대기 (API rate limit 회피)
            if i % self.batch_size == 0 and i < len(test_cases):
                print(f"⏸️  배치 완료 ({i}/{len(test_cases)}). {self.delay_seconds}초 대기 중...\n")
                time.sleep(self.delay_seconds)

    def _test_single_query(self, test_case: Dict, category: str) -> Dict[str, Any]:
        """단일 쿼리 테스트"""
        result = {
            'id': test_case['id'],
            'category': category,
            'query': test_case['query'],
            'expected_features': test_case['expected_features'],
            'timestamp': datetime.now().isoformat(),
            'sql_generated': False,
            'generated_sql': None,
            'execution_attempted': False,
            'executed': False,
            'execution_success': False,
            'row_count': None,
            'execution_time': None,
            'error_message': None,
            'feature_matches': [],
            'feature_match_rate': 0.0
        }

        # Step 1: SQL 생성
        try:
            nl2sql_result = self.generator.generate_sql(test_case['query'])

            if nl2sql_result.success:
                result['sql_generated'] = True
                result['generated_sql'] = nl2sql_result.sql_query

                # Feature 매칭 검사
                matches = [
                    feature for feature in test_case['expected_features']
                    if feature.lower() in nl2sql_result.sql_query.lower()
                ]
                result['feature_matches'] = matches
                result['feature_match_rate'] = len(matches) / len(test_case['expected_features'])
            else:
                result['error_message'] = nl2sql_result.error_message
                return result

        except Exception as e:
            result['error_message'] = f"SQL 생성 중 예외: {str(e)}"
            return result

        # Step 2: SQL 실행 (생성 성공 시만)
        if result['sql_generated']:
            result['execution_attempted'] = True
            try:
                exec_result = self.databricks.execute_query(result['generated_sql'])

                if exec_result['success']:
                    result['executed'] = True
                    result['execution_success'] = True
                    result['row_count'] = exec_result['row_count']
                    result['execution_time'] = exec_result.get('execution_time')
                else:
                    result['executed'] = True
                    result['execution_success'] = False
                    result['error_message'] = exec_result.get('error')

            except Exception as e:
                result['executed'] = True
                result['execution_success'] = False
                result['error_message'] = f"실행 중 예외: {str(e)}"

        return result

    def _calculate_summary(self, duration: float) -> Dict[str, Any]:
        """결과 통계 계산"""
        total = len(self.results)
        sql_generated = sum(1 for r in self.results if r['sql_generated'])
        executed = sum(1 for r in self.results if r['executed'])
        execution_success = sum(1 for r in self.results if r['execution_success'])

        # Category별 통계
        category_stats = {}
        for category in self.test_cases.keys():
            cat_results = [r for r in self.results if r['category'] == category]
            category_stats[category] = {
                'total': len(cat_results),
                'sql_generated': sum(1 for r in cat_results if r['sql_generated']),
                'execution_success': sum(1 for r in cat_results if r['execution_success']),
                'avg_feature_match': sum(r['feature_match_rate'] for r in cat_results) / len(cat_results) if cat_results else 0
            }

        # Feature matching 통계
        avg_feature_match = sum(r['feature_match_rate'] for r in self.results) / total if total > 0 else 0

        return {
            'test_date': datetime.now().isoformat(),
            'total_duration_seconds': round(duration, 2),
            'total_tests': total,
            'sql_generation': {
                'success_count': sql_generated,
                'failure_count': total - sql_generated,
                'success_rate': round(sql_generated / total * 100, 2) if total > 0 else 0
            },
            'execution': {
                'attempted': executed,
                'success_count': execution_success,
                'failure_count': executed - execution_success,
                'success_rate': round(execution_success / executed * 100, 2) if executed > 0 else 0
            },
            'feature_matching': {
                'avg_match_rate': round(avg_feature_match * 100, 2)
            },
            'category_breakdown': category_stats,
            'detailed_results': self.results
        }

    def _save_results(self, summary: Dict[str, Any]):
        """결과 저장"""
        output_dir = Path(__file__).parent / "results"
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"nl2sql_test_results_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n💾 결과 저장: {output_file}")

    def _print_summary(self, summary: Dict[str, Any]):
        """최종 리포트 출력"""
        print("\n" + "=" * 80)
        print("📊 Phase 15 Test Results Summary")
        print("=" * 80)

        print(f"\n⏱️  총 소요 시간: {summary['total_duration_seconds']}초")
        print(f"📝 총 테스트: {summary['total_tests']}개\n")

        print("🔹 SQL 생성 성공률")
        print(f"   성공: {summary['sql_generation']['success_count']}개")
        print(f"   실패: {summary['sql_generation']['failure_count']}개")
        print(f"   성공률: {summary['sql_generation']['success_rate']}%\n")

        print("🔹 SQL 실행 성공률")
        print(f"   시도: {summary['execution']['attempted']}개")
        print(f"   성공: {summary['execution']['success_count']}개")
        print(f"   실패: {summary['execution']['failure_count']}개")
        print(f"   성공률: {summary['execution']['success_rate']}%\n")

        print(f"🔹 Feature 매칭률: {summary['feature_matching']['avg_match_rate']}%\n")

        print("📂 Category별 결과:")
        for category, stats in summary['category_breakdown'].items():
            print(f"   {category}:")
            print(f"      SQL 생성: {stats['sql_generated']}/{stats['total']}")
            print(f"      실행 성공: {stats['execution_success']}/{stats['total']}")
            print(f"      Feature 매칭: {stats['avg_feature_match']:.1%}")

        print("\n" + "=" * 80)

        # 목표 달성 여부
        sql_target = 84
        exec_target = 90
        sql_rate = summary['sql_generation']['success_rate']
        exec_rate = summary['execution']['success_rate']

        print("\n🎯 목표 달성 여부:")
        print(f"   SQL 생성 성공률: {sql_rate}% (목표: {sql_target}%+) {'✅' if sql_rate >= sql_target else '❌'}")
        print(f"   실행 성공률: {exec_rate}% (목표: {exec_target}%+) {'✅' if exec_rate >= exec_target else '❌'}")


if __name__ == "__main__":
    tester = NL2SQLTester(batch_size=5, delay_seconds=10)
    summary = tester.run_all_tests()
