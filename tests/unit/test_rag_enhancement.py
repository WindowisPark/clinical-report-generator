"""
RAG Enhancement Test - Complex Queries
RAG 질병 코드 시스템의 효과를 검증하는 5개 복잡 쿼리 테스트
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipelines.nl2sql_generator import NL2SQLGenerator


def load_test_cases():
    """테스트 케이스 로드"""
    test_file = project_root / "tests" / "data" / "rag_test_queries.json"
    with open(test_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_sql(sql: str, validation: dict) -> dict:
    """SQL 검증"""
    sql_lower = sql.lower()
    results = {
        "passed": True,
        "failures": []
    }

    # Must-have tables 검증
    for table in validation.get("must_have_tables", []):
        if table.lower() not in sql_lower:
            results["passed"] = False
            results["failures"].append(f"Missing table: {table}")

    # Must-have keywords 검증
    for keyword in validation.get("must_have_keywords", []):
        if keyword.lower() not in sql_lower:
            results["passed"] = False
            results["failures"].append(f"Missing keyword: {keyword}")

    # JOIN 검증
    if validation.get("must_have_join"):
        join_key = validation["must_have_join"].lower()
        if join_key not in sql_lower:
            results["passed"] = False
            results["failures"].append(f"Missing join key: {join_key}")

    return results


def check_disease_code_usage(sql: str) -> dict:
    """질병 코드 사용 여부 체크"""
    sql_lower = sql.lower()
    uses_code = 'res_disease_code' in sql_lower
    uses_name = 'res_disease_name' in sql_lower

    # 사용된 질병 코드 패턴 추출
    disease_codes = []
    if uses_code:
        import re
        patterns = re.findall(r"res_disease_code\s+LIKE\s+'([A-Z0-9_%]+)'", sql, re.IGNORECASE)
        disease_codes = list(set(patterns))

    return {
        "uses_disease_code": uses_code,
        "uses_disease_name": uses_name,
        "optimized": uses_code and not uses_name,
        "disease_codes_found": disease_codes
    }


def run_tests():
    """RAG 테스트 실행"""
    print("=" * 80)
    print("RAG Enhancement Test - Complex Query Validation")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 초기화
    generator = NL2SQLGenerator()

    # 테스트 케이스 로드
    test_cases = load_test_cases()
    print(f"📋 Loaded {len(test_cases)} complex test cases\n")

    # 결과 저장
    results = {
        "total": len(test_cases),
        "sql_generated": 0,
        "sql_validated": 0,
        "disease_code_detected": 0,
        "disease_code_used": 0,
        "failures": [],
        "details": []
    }

    # 테스트 실행
    print("Running tests...")
    print("-" * 80)

    for idx, case in enumerate(test_cases, 1):
        query = case["query"]
        category = case["category"]
        description = case["description"]
        validation = case["validation"]

        print(f"\n[{idx}/{len(test_cases)}] {category}")
        print(f"  Query: {query}")
        print(f"  Description: {description}")

        # SQL 생성
        result = generator.generate_sql(query)

        test_detail = {
            "query": query,
            "category": category,
            "success": result.success
        }

        if not result.success:
            results["failures"].append({
                "query": query,
                "category": category,
                "stage": "generation",
                "error": result.error_message
            })
            print(f"  ❌ Generation failed: {result.error_message}")
            test_detail["error"] = result.error_message
            results["details"].append(test_detail)
            continue

        results["sql_generated"] += 1
        print(f"  ✅ SQL generated")

        # 질병 코드 사용 확인
        code_usage = check_disease_code_usage(result.sql_query)
        test_detail["code_usage"] = code_usage

        if code_usage["disease_codes_found"]:
            results["disease_code_detected"] += 1
            print(f"  🔍 RAG detected disease codes: {code_usage['disease_codes_found']}")

        if code_usage["optimized"]:
            results["disease_code_used"] += 1
            print(f"  💡 Disease code used (optimized)")
        elif code_usage["uses_disease_name"]:
            print(f"  ⚠️ Using disease name instead of code (slower)")

        # SQL 검증
        validation_result = validate_sql(result.sql_query, validation)
        test_detail["validation"] = validation_result

        if validation_result["passed"]:
            results["sql_validated"] += 1
            print(f"  ✅ Validation passed")
        else:
            results["failures"].append({
                "query": query,
                "category": category,
                "stage": "validation",
                "error": ", ".join(validation_result["failures"])
            })
            print(f"  ❌ Validation failed: {', '.join(validation_result['failures'])}")

        # SQL 출력 (처음 300자)
        print(f"\n  Generated SQL (preview):")
        sql_preview = result.sql_query[:300] + "..." if len(result.sql_query) > 300 else result.sql_query
        for line in sql_preview.split('\n'):
            print(f"    {line}")

        results["details"].append(test_detail)

    # 결과 리포트
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)

    print(f"\n📊 Overall Statistics:")
    print(f"  Total test cases: {results['total']}")
    print(f"  SQL generated: {results['sql_generated']} ({results['sql_generated']/results['total']*100:.1f}%)")
    print(f"  SQL validated: {results['sql_validated']} ({results['sql_validated']/results['total']*100:.1f}%)")
    print(f"  RAG disease code detected: {results['disease_code_detected']} ({results['disease_code_detected']/results['total']*100:.1f}%)")
    print(f"  Disease code used: {results['disease_code_used']} ({results['disease_code_used']/results['sql_generated']*100 if results['sql_generated'] > 0 else 0:.1f}% of generated)")

    if results["failures"]:
        print(f"\n❌ Failures ({len(results['failures'])}):")
        for failure in results["failures"]:
            print(f"\n  [{failure['category']}] {failure['query'][:60]}...")
            print(f"    Stage: {failure['stage']}")
            print(f"    Error: {failure['error']}")

    # RAG 효과 분석
    print("\n" + "=" * 80)
    print("RAG EFFECTIVENESS ANALYSIS")
    print("=" * 80)

    rag_success_rate = results['disease_code_detected'] / results['total'] * 100 if results['total'] > 0 else 0
    code_usage_rate = results['disease_code_used'] / results['sql_generated'] * 100 if results['sql_generated'] > 0 else 0

    print(f"\n  RAG Detection Rate: {rag_success_rate:.1f}% (Target: 100% for disease queries)")
    print(f"    {'✅ EXCELLENT' if rag_success_rate >= 80 else '⚠️ NEEDS IMPROVEMENT'}")

    print(f"\n  Disease Code Usage: {code_usage_rate:.1f}% (Target: 100%)")
    print(f"    {'✅ EXCELLENT' if code_usage_rate >= 80 else '⚠️ NEEDS IMPROVEMENT'}")

    # 성공 기준 평가
    print("\n" + "=" * 80)
    print("SUCCESS CRITERIA EVALUATION")
    print("=" * 80)

    gen_rate = results['sql_generated'] / results['total'] * 100
    val_rate = results['sql_validated'] / results['total'] * 100 if results['total'] > 0 else 0

    print(f"\n  SQL Generation Rate: {gen_rate:.1f}% (Target: 100%)")
    print(f"    {'✅ PASS' if gen_rate >= 100 else '❌ FAIL'}")

    print(f"\n  SQL Validation Rate: {val_rate:.1f}% (Target: 80%+)")
    print(f"    {'✅ PASS' if val_rate >= 80 else '❌ FAIL'}")

    print(f"\n  RAG Detection + Usage: {code_usage_rate:.1f}% (Target: 80%+)")
    print(f"    {'✅ PASS' if code_usage_rate >= 80 else '❌ FAIL'}")

    overall_pass = gen_rate >= 100 and val_rate >= 80 and code_usage_rate >= 80
    print(f"\n{'🎉 OVERALL: PASS' if overall_pass else '⚠️ OVERALL: NEEDS IMPROVEMENT'}")

    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return results


if __name__ == "__main__":
    results = run_tests()

    # Exit code
    gen_rate = results['sql_generated'] / results['total'] * 100
    val_rate = results['sql_validated'] / results['total'] * 100
    code_usage_rate = results['disease_code_used'] / results['sql_generated'] * 100 if results['sql_generated'] > 0 else 0

    overall_pass = gen_rate >= 100 and val_rate >= 80 and code_usage_rate >= 80
    sys.exit(0 if overall_pass else 1)
