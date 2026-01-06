"""단일 쿼리 상세 분석"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from pipelines.nl2sql_generator import NL2SQLGenerator

# WF-01: 각 질병별로 환자 수 순위를 매겨줘 (RANK 사용)
query = "각 질병별로 환자 수 순위를 매겨줘 (RANK 사용)"

print("=" * 80)
print(f"Query: {query}")
print("=" * 80)
print()

generator = NL2SQLGenerator(enable_logging=False)
result = generator.generate_sql(query)

if result.success:
    print("✅ SQL 생성 성공\n")
    print("생성된 SQL:")
    print("-" * 80)
    print(result.sql_query)
    print("-" * 80)

    print("\nFeature 확인:")
    sql_lower = result.sql_query.lower()

    features = {
        "RANK()": "rank()" in sql_lower,
        "OVER": "over" in sql_lower,
        "PARTITION BY": "partition by" in sql_lower,
        "ORDER BY": "order by" in sql_lower,
    }

    for feature, found in features.items():
        print(f"  {feature}: {'✅' if found else '❌'}")

    # PARTITION BY가 왜 없는지 확인
    if not features["PARTITION BY"]:
        print("\n🔍 PARTITION BY가 없는 이유:")
        if "rank() over (order by" in sql_lower:
            print("  → 질병별 전체 순위 (PARTITION BY 불필요)")
            print("  → 만약 질병 그룹 내 순위가 필요하면 PARTITION BY 필요")
else:
    print(f"❌ SQL 생성 실패: {result.error_message}")
