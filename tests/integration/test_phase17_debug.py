"""
Phase 17 디버깅: Few-shot 예시 선택 확인
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from pipelines.nl2sql_generator import NL2SQLGenerator

def test_example_selection():
    """Few-shot 예시가 제대로 선택되고 있는지 확인"""

    generator = NL2SQLGenerator(enable_logging=False)

    # MTJ-02: 서울 지역 65세 이상 환자의 평균 처방 약품 수
    test_query = "서울 지역 65세 이상 환자의 평균 처방 약품 수는?"

    print("=" * 80)
    print("🔍 Few-shot 예시 선택 디버깅")
    print("=" * 80)
    print(f"\n쿼리: {test_query}\n")

    # 키워드 추출
    keywords = generator._extract_keywords(test_query)
    print(f"추출된 키워드: {keywords}")

    # 예시 선택
    examples = generator._select_relevant_examples(test_query, keywords)
    print(f"\n선택된 예시 수: {len(examples)}개\n")

    for i, ex in enumerate(examples, 1):
        print(f"예시 {i}:")
        print(f"  질문: {ex['question']}")
        print(f"  테이블: {ex['tables']}")
        print()

    # SQL 생성
    print("=" * 80)
    print("SQL 생성 중...")
    print("=" * 80)
    result = generator.generate_sql(test_query)

    if result.success:
        print("\n✅ SQL 생성 성공\n")
        print("생성된 SQL:")
        print("-" * 80)
        print(result.sql_query)
        print("-" * 80)

        # Feature 체크
        sql_lower = result.sql_query.lower()
        features = {
            "JOIN": "join" in sql_lower,
            "TO_DATE(birthday": "to_date(birthday" in sql_lower or "try_to_date(birthday" in sql_lower or "to_date(ip.birthday" in sql_lower or "try_to_date(ip.birthday" in sql_lower,
            "res_city LIKE '%서울%'": "res_city like" in sql_lower or "res_hospital_name like '%서울%'" in sql_lower
        }

        print("\nFeature 체크:")
        for feature, found in features.items():
            print(f"  {feature}: {'✅' if found else '❌'}")
    else:
        print(f"\n❌ SQL 생성 실패: {result.error_message}")

if __name__ == "__main__":
    test_example_selection()
