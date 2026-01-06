"""
RAG SQL Execution Test
생성된 SQL을 Databricks에서 실제 실행하여 검증
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipelines.nl2sql_generator import NL2SQLGenerator
from services.databricks_client import DatabricksClient


def load_test_cases():
    """테스트 케이스 로드"""
    test_file = project_root / "tests" / "data" / "rag_test_queries.json"
    with open(test_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_execution_tests():
    """SQL 실행 테스트"""
    print("=" * 80)
    print("RAG SQL Execution Test - Databricks Validation")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 초기화
    generator = NL2SQLGenerator()

    try:
        client = DatabricksClient()
        print("✅ Databricks client initialized\n")
    except Exception as e:
        print(f"❌ Databricks client initialization failed: {e}")
        print("Cannot proceed without database connection.")
        return None

    # 테스트 케이스 로드
    test_cases = load_test_cases()
    print(f"📋 Loaded {len(test_cases)} test cases\n")

    # 결과 저장
    results = {
        "total": len(test_cases),
        "sql_generated": 0,
        "sql_executed": 0,
        "sql_succeeded": 0,
        "execution_details": []
    }

    # 테스트 실행
    print("Running execution tests...")
    print("-" * 80)

    for idx, case in enumerate(test_cases, 1):
        query = case["query"]
        category = case["category"]

        print(f"\n[{idx}/{len(test_cases)}] {category}")
        print(f"Query: {query}\n")

        # 1. SQL 생성
        result = generator.generate_sql(query)

        detail = {
            "query": query,
            "category": category,
            "sql_generated": result.success
        }

        if not result.success:
            print(f"  ❌ SQL generation failed: {result.error_message}\n")
            detail["generation_error"] = result.error_message
            results["execution_details"].append(detail)
            continue

        results["sql_generated"] += 1
        detail["sql_query"] = result.sql_query

        print(f"  ✅ SQL generated")
        print(f"\n  Generated SQL:")
        for line in result.sql_query.split('\n')[:20]:  # 처음 20줄만
            print(f"    {line}")
        if len(result.sql_query.split('\n')) > 20:
            print(f"    ... ({len(result.sql_query.split('\n')) - 20} more lines)")

        # 2. Databricks 실행
        print(f"\n  🔄 Executing on Databricks...")

        try:
            exec_result = client.execute_query(result.sql_query, max_rows=100)
            results["sql_executed"] += 1

            detail["executed"] = True
            detail["execution_success"] = exec_result['success']
            detail["execution_time"] = exec_result.get('execution_time', 0)
            detail["row_count"] = exec_result.get('row_count', 0)

            if exec_result['success']:
                results["sql_succeeded"] += 1
                print(f"  ✅ Execution succeeded!")
                print(f"     - Rows returned: {exec_result['row_count']}")
                print(f"     - Execution time: {exec_result['execution_time']:.2f}s")

                # 결과 미리보기
                if exec_result['data'] is not None and not exec_result['data'].empty:
                    print(f"\n  📊 Result Preview (first 3 rows):")
                    print(exec_result['data'].head(3).to_string(index=False))

                detail["success"] = True
            else:
                print(f"  ❌ Execution failed: {exec_result['error_message']}")
                detail["execution_error"] = exec_result['error_message']
                detail["success"] = False

        except Exception as e:
            print(f"  ❌ Execution error: {str(e)}")
            detail["executed"] = False
            detail["execution_error"] = str(e)
            detail["success"] = False

        results["execution_details"].append(detail)
        print()

    # 결과 리포트
    print("\n" + "=" * 80)
    print("EXECUTION TEST RESULTS")
    print("=" * 80)

    print(f"\n📊 Overall Statistics:")
    print(f"  Total test cases: {results['total']}")
    print(f"  SQL generated: {results['sql_generated']}/{results['total']} ({results['sql_generated']/results['total']*100:.1f}%)")
    print(f"  SQL executed: {results['sql_executed']}/{results['sql_generated']} ({results['sql_executed']/results['sql_generated']*100 if results['sql_generated'] > 0 else 0:.1f}%)")
    print(f"  Execution succeeded: {results['sql_succeeded']}/{results['sql_executed']} ({results['sql_succeeded']/results['sql_executed']*100 if results['sql_executed'] > 0 else 0:.1f}%)")

    # 카테고리별 성공률
    print(f"\n📈 By Category:")
    categories = {}
    for detail in results["execution_details"]:
        cat = detail["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "success": 0}
        categories[cat]["total"] += 1
        if detail.get("success"):
            categories[cat]["success"] += 1

    for cat, stats in categories.items():
        success_rate = stats["success"] / stats["total"] * 100
        print(f"  {cat}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

    # 실패 케이스
    failures = [d for d in results["execution_details"] if not d.get("success", False)]
    if failures:
        print(f"\n❌ Failed Cases ({len(failures)}):")
        for fail in failures:
            print(f"\n  [{fail['category']}]")
            print(f"  Query: {fail['query'][:80]}...")
            if 'generation_error' in fail:
                print(f"  Generation Error: {fail['generation_error']}")
            elif 'execution_error' in fail:
                print(f"  Execution Error: {fail['execution_error'][:200]}")

    # 실행 시간 분석
    executed_cases = [d for d in results["execution_details"] if d.get("execution_success")]
    if executed_cases:
        avg_time = sum(d["execution_time"] for d in executed_cases) / len(executed_cases)
        max_time = max(d["execution_time"] for d in executed_cases)
        min_time = min(d["execution_time"] for d in executed_cases)

        print(f"\n⏱️ Execution Time Analysis:")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Min: {min_time:.2f}s")
        print(f"  Max: {max_time:.2f}s")

    # 성공 기준
    print("\n" + "=" * 80)
    print("SUCCESS CRITERIA")
    print("=" * 80)

    gen_rate = results['sql_generated'] / results['total'] * 100
    exec_rate = results['sql_succeeded'] / results['sql_generated'] * 100 if results['sql_generated'] > 0 else 0

    print(f"\n  SQL Generation: {gen_rate:.1f}% (Target: 100%)")
    print(f"    {'✅ PASS' if gen_rate >= 100 else '❌ FAIL'}")

    print(f"\n  SQL Execution Success: {exec_rate:.1f}% (Target: 80%+)")
    print(f"    {'✅ PASS' if exec_rate >= 80 else '❌ FAIL'}")

    overall_pass = gen_rate >= 100 and exec_rate >= 80
    print(f"\n{'🎉 OVERALL: PASS' if overall_pass else '⚠️ OVERALL: FAIL'}")

    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return results


if __name__ == "__main__":
    results = run_execution_tests()

    if results is None:
        sys.exit(1)

    # Exit code
    gen_rate = results['sql_generated'] / results['total'] * 100
    exec_rate = results['sql_succeeded'] / results['sql_generated'] * 100 if results['sql_generated'] > 0 else 0

    overall_pass = gen_rate >= 100 and exec_rate >= 80
    sys.exit(0 if overall_pass else 1)
