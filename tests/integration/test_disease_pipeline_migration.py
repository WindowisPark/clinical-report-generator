"""
Tab 2 (Disease Pipeline) PromptLoader 마이그레이션 테스트
"""

from pipelines.disease_pipeline import DiseaseAnalysisPipeline

def test_disease_pipeline_with_prompt_loader():
    """PromptLoader를 사용한 Disease Pipeline 테스트"""

    print("=" * 80)
    print("Tab 2 (Disease Pipeline) PromptLoader 마이그레이션 테스트")
    print("=" * 80)

    # Pipeline 초기화
    pipeline = DiseaseAnalysisPipeline()

    # 테스트 질환들
    test_diseases = [
        "고혈압",
        "당뇨병",
        "천식"
    ]

    success_count = 0

    for i, disease in enumerate(test_diseases, 1):
        print(f"\n{'='*80}")
        print(f"테스트 {i}/{len(test_diseases)}: {disease}")
        print("=" * 80)

        try:
            # 추가 레시피 추천
            recommendations = pipeline.recommend_additional_recipes(
                disease_name=disease,
                target_count=7
            )

            if recommendations and len(recommendations) > 0:
                print(f"✅ 성공! {len(recommendations)}개 레시피 추천됨")
                print(f"\n📋 추천 레시피:")
                for j, recipe_name in enumerate(recommendations, 1):
                    print(f"  {j}. {recipe_name}")

                success_count += 1
            else:
                print(f"❌ 실패: 추천 결과 없음")

        except Exception as e:
            print(f"❌ 에러 발생: {str(e)}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*80}")
    print(f"테스트 결과: {success_count}/{len(test_diseases)} 성공 ({success_count/len(test_diseases)*100:.1f}%)")
    print("=" * 80)

    if success_count == len(test_diseases):
        print("\n✅ Tab 2 마이그레이션 성공! 모든 테스트 통과")
        return True
    else:
        print(f"\n⚠️  {len(test_diseases) - success_count}개 테스트 실패")
        return False

if __name__ == "__main__":
    test_disease_pipeline_with_prompt_loader()
