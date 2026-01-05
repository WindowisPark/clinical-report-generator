"""
CA-02 테스트 케이스 재실행
GROUP BY 검증 규칙 추가 후 효과 확인
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from pipelines.nl2sql_generator import NL2SQLGenerator
from services.databricks_client import DatabricksClient

def test_ca02():
    """
    원래 실패한 케이스: "지역별로 가장 많은 질병 TOP 3을 찾아줘"
    에러: [MISSING_AGGREGATION] GROUP BY 누락
    """
    print("=" * 80)
    print("CA-02 재테스트: GROUP BY Validation")
    print("=" * 80)
    print()
    
    query = "지역별로 가장 많은 질병 TOP 3을 찾아줘"
    print(f"🔍 Query: {query}\n")
    
    # Step 1: SQL 생성
    print("Step 1: SQL 생성 중...")
    generator = NL2SQLGenerator()
    result = generator.generate_sql(query)
    
    if not result.success:
        print(f"❌ SQL 생성 실패: {result.error_message}")
        return False
    
    print("✅ SQL 생성 성공\n")
    print("생성된 SQL:")
    print("-" * 80)
    print(result.sql_query)
    print("-" * 80)
    print()
    
    # Step 2: GROUP BY 분석
    print("Step 2: GROUP BY 분석...")
    sql_lower = result.sql_query.lower()
    
    has_group_by = "group by" in sql_lower
    has_row_number = "row_number()" in sql_lower
    has_case_when = "case when" in sql_lower
    
    print(f"  - GROUP BY 사용: {'✅' if has_group_by else '❌'}")
    print(f"  - ROW_NUMBER() 사용: {'✅' if has_row_number else '❌'}")
    print(f"  - CASE WHEN 사용: {'✅' if has_case_when else '❌'}")
    
    if has_row_number and has_group_by:
        print("  ⚠️  ROW_NUMBER() + GROUP BY 조합 → 서브쿼리 구조 확인 필요")
    print()
    
    # Step 3: Databricks 실행
    print("Step 3: Databricks 실행 중...")
    databricks = DatabricksClient()
    exec_result = databricks.execute_query(result.sql_query)
    
    if not exec_result['success']:
        print(f"❌ 실행 실패: {exec_result.get('error', 'Unknown error')}")
        print()
        
        # 에러 분석
        error_msg = exec_result.get('error', '')
        if 'MISSING_AGGREGATION' in error_msg:
            print("🔍 에러 분석: GROUP BY 정합성 문제 여전히 존재")
            print("   → 프롬프트 강화로 해결되지 않음")
            print("   → Post-validation 로직 추가 필요")
        elif 'MISSING_GROUP_BY' in error_msg:
            print("🔍 에러 분석: GROUP BY 절 누락")
        else:
            print(f"🔍 에러 분석: 다른 문제 발생 - {error_msg[:200]}")
        
        return False
    
    print(f"✅ 실행 성공!")
    print(f"   - 실행 시간: {exec_result.get('execution_time', 'N/A')}초")
    print(f"   - 결과 행 수: {exec_result.get('row_count', 'N/A')}개")
    print()
    
    # 결과 샘플 표시
    if exec_result.get('data'):
        print("결과 샘플 (최대 10개):")
        print("-" * 80)
        for i, row in enumerate(exec_result['data'][:10], 1):
            print(f"{i}. {row}")
        print("-" * 80)
    
    return True

if __name__ == "__main__":
    success = test_ca02()
    
    print()
    print("=" * 80)
    if success:
        print("🎉 CA-02 테스트 통과! GROUP BY 검증 규칙 효과 확인됨")
        print("   → Phase 15에서 실패했던 케이스가 이제 성공")
        print("   → 실행 성공률: 96% (24/25) → 100% (25/25) 예상")
    else:
        print("⚠️  CA-02 테스트 실패 - 추가 조치 필요")
        print("   → 옵션 1: Few-shot 예시에 GROUP BY 복잡 케이스 추가")
        print("   → 옵션 2: Post-validation 로직 구현")
    print("=" * 80)
