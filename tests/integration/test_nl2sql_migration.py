"""
Tab 3 (NL2SQL) PromptLoader 마이그레이션 테스트
"""

from pipelines.nl2sql_generator import NL2SQLGenerator

def test_nl2sql_with_prompt_loader():
    """PromptLoader를 사용한 NL2SQL 테스트"""

    print("=" * 80)
    print("Tab 3 (NL2SQL) PromptLoader 마이그레이션 테스트")
    print("=" * 80)

    # Generator 초기화
    generator = NL2SQLGenerator()

    # 테스트 쿼리
    test_queries = [
        "고혈압 환자의 성별 분포를 보여주세요",
        "서울 지역 당뇨병 환자에게 처방된 약물 TOP 5",
        "최근 1년간 신규 환자 수 추이를 월별로 집계해주세요"
    ]

    success_count = 0

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"테스트 {i}/{len(test_queries)}: {query}")
        print("=" * 80)

        try:
            result = generator.generate_sql(query)

            if result.success:
                print(f"✅ 성공!")
                print(f"\n📊 분석:")
                print(f"  - Intent: {result.analysis.get('intent', 'N/A')}")
                print(f"  - Tables: {result.analysis.get('required_tables', [])}")

                print(f"\n📝 생성된 SQL:")
                print(result.sql_query[:500])  # 처음 500자만 출력
                if len(result.sql_query) > 500:
                    print(f"... ({len(result.sql_query) - 500} more characters)")

                success_count += 1
            else:
                print(f"❌ 실패: {result.error_message}")

        except Exception as e:
            print(f"❌ 에러 발생: {str(e)}")

    print(f"\n{'='*80}")
    print(f"테스트 결과: {success_count}/{len(test_queries)} 성공 ({success_count/len(test_queries)*100:.1f}%)")
    print("=" * 80)

    if success_count == len(test_queries):
        print("\n✅ Tab 3 마이그레이션 성공! 모든 테스트 통과")
        return True
    else:
        print(f"\n⚠️  {len(test_queries) - success_count}개 테스트 실패")
        return False

if __name__ == "__main__":
    test_nl2sql_with_prompt_loader()
