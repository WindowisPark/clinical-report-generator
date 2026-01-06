"""
Phase 17 개선 효과 테스트
- GROUP BY 검증 강화 (프롬프트)
- Few-shot 예시 확장 (5개 → 10개)
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from pipelines.nl2sql_generator import NL2SQLGenerator

def test_feature_matching():
    """Feature 매칭률이 낮았던 쿼리들 재테스트"""
    
    generator = NL2SQLGenerator(enable_logging=False)
    
    # Phase 15에서 Feature 매칭률이 낮았던 쿼리들
    test_cases = [
        {
            "id": "MTJ-02",
            "query": "서울 지역 65세 이상 환자의 평균 처방 약품 수는?",
            "expected_features": ["JOIN", "TO_DATE(birthday", "LIKE '%서울%'"],
            "phase15_match_rate": 33.3
        },
        {
            "id": "MTJ-05",
            "query": "2020년 이후 진료받은 환자의 지역별 평균 연령은?",
            "expected_features": ["JOIN", "TRY_TO_DATE(res_treat_start_date", "TRY_TO_DATE(birthday", "GROUP BY"],
            "phase15_match_rate": 25.0
        },
        {
            "id": "WF-02",
            "query": "지역별 환자 수를 계산하고 전체 환자 대비 비율도 같이 보여줘",
            "expected_features": ["COUNT", "SUM", "OVER()", "GROUP BY"],
            "phase15_match_rate": 25.0
        },
        {
            "id": "WF-01",
            "query": "각 질병별로 환자 수 순위를 매겨줘 (RANK 사용)",
            "expected_features": ["RANK()", "OVER", "PARTITION BY", "ORDER BY"],
            "phase15_match_rate": 75.0
        },
        {
            "id": "CA-01",
            "query": "성별, 연령대별 환자 수를 교차 집계해줘",
            "expected_features": ["GROUP BY", "CASE WHEN", "TRY_TO_DATE(birthday", "gender"],
            "phase15_match_rate": 50.0
        }
    ]
    
    print("=" * 80)
    print("Phase 17: Feature Matching Improvement Test")
    print("=" * 80)
    print(f"\n테스트 케이스: {len(test_cases)}개")
    print("목표: Feature 매칭률 개선 확인\n")
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {test_case['id']}: {test_case['query']}")
        print(f"  Phase 15 매칭률: {test_case['phase15_match_rate']}%")
        
        # SQL 생성
        result = generator.generate_sql(test_case['query'])
        
        if not result.success:
            print(f"  ❌ SQL 생성 실패: {result.error_message}")
            results.append({
                **test_case,
                'phase17_match_rate': 0.0,
                'improvement': -test_case['phase15_match_rate']
            })
            continue
        
        # Feature 매칭 검사
        sql_lower = result.sql_query.lower()
        matched_features = []
        
        for feature in test_case['expected_features']:
            if feature.lower() in sql_lower:
                matched_features.append(feature)
        
        match_rate = (len(matched_features) / len(test_case['expected_features'])) * 100
        improvement = match_rate - test_case['phase15_match_rate']
        
        print(f"  Phase 17 매칭률: {match_rate:.1f}% ({len(matched_features)}/{len(test_case['expected_features'])})")
        print(f"  개선: {improvement:+.1f}%p")
        
        if matched_features:
            print(f"  매칭된 Feature: {', '.join(matched_features)}")
        
        missing = [f for f in test_case['expected_features'] if f not in matched_features]
        if missing:
            print(f"  누락된 Feature: {', '.join(missing)}")
        
        results.append({
            **test_case,
            'phase17_match_rate': match_rate,
            'matched_features': matched_features,
            'improvement': improvement
        })
    
    # 전체 통계
    print("\n" + "=" * 80)
    print("📊 Phase 17 개선 효과 요약")
    print("=" * 80)
    
    avg_phase15 = sum(r['phase15_match_rate'] for r in results) / len(results)
    avg_phase17 = sum(r['phase17_match_rate'] for r in results) / len(results)
    avg_improvement = avg_phase17 - avg_phase15
    
    print(f"\n평균 Feature 매칭률:")
    print(f"  Phase 15: {avg_phase15:.1f}%")
    print(f"  Phase 17: {avg_phase17:.1f}%")
    print(f"  개선: {avg_improvement:+.1f}%p")
    
    # 개선된 케이스
    improved = [r for r in results if r['improvement'] > 0]
    print(f"\n개선된 케이스: {len(improved)}/{len(results)}개")
    
    if improved:
        print("\n개선 상세:")
        for r in improved:
            print(f"  {r['id']}: {r['phase15_match_rate']:.1f}% → {r['phase17_match_rate']:.1f}% ({r['improvement']:+.1f}%p)")
    
    # 여전히 낮은 케이스
    low_performers = [r for r in results if r['phase17_match_rate'] < 70]
    if low_performers:
        print(f"\n⚠️  여전히 낮은 매칭률 (< 70%):")
        for r in low_performers:
            print(f"  {r['id']}: {r['phase17_match_rate']:.1f}%")
    
    print("\n" + "=" * 80)
    
    # 목표 달성 여부
    target = 85.0
    if avg_phase17 >= target:
        print(f"🎉 목표 달성! 평균 매칭률 {avg_phase17:.1f}% >= {target}%")
    else:
        print(f"⚠️  목표 미달성: 평균 매칭률 {avg_phase17:.1f}% < {target}%")
        print(f"   추가 {target - avg_phase17:.1f}%p 개선 필요")
    
    return results

if __name__ == "__main__":
    test_feature_matching()
