#!/usr/bin/env python3
"""
Test script for PromptLoader

Run this to verify the prompt system is working correctly:
    python test_prompt_loader.py
"""

import json
from pathlib import Path
from prompts.loader import PromptLoader


def test_file_structure():
    """Verify all prompt files exist"""
    print("=" * 60)
    print("TEST 1: File Structure")
    print("=" * 60)

    required_files = [
        "prompts/__init__.py",
        "prompts/loader.py",
        "prompts/shared/databricks_rules.txt",
        "prompts/shared/output_validation.txt",
        "prompts/shared/schema_formatting.txt",
        "prompts/report_generation/system.txt",
        "prompts/report_generation/user_template.txt",
        "prompts/report_generation/examples.json",
        "prompts/recipe_recommendation/system.txt",
        "prompts/recipe_recommendation/user_template.txt",
        "prompts/nl2sql/system.txt",
        "prompts/nl2sql/user_template.txt",
        "prompts/nl2sql/examples.json",
    ]

    all_exist = True
    for file_path in required_files:
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        all_exist = all_exist and exists

    if all_exist:
        print("\n✅ All files exist!\n")
    else:
        print("\n❌ Some files are missing!\n")
        return False

    return True


def test_shared_components():
    """Test loading shared components"""
    print("=" * 60)
    print("TEST 2: Shared Components")
    print("=" * 60)

    loader = PromptLoader()

    # Test databricks_rules
    databricks_rules = loader._get_shared_component("databricks_rules")
    assert "TO_DATE" in databricks_rules, "databricks_rules missing TO_DATE"
    assert "CHAR(200)" in databricks_rules, "databricks_rules missing CHAR(200)"
    print("✅ databricks_rules.txt loaded successfully")
    print(f"   Length: {len(databricks_rules)} characters")

    # Test output_validation
    output_validation = loader._get_shared_component("output_validation")
    assert "JSON" in output_validation, "output_validation missing JSON"
    print("✅ output_validation.txt loaded successfully")
    print(f"   Length: {len(output_validation)} characters")

    # Test schema_formatting
    schema_formatting = loader._get_shared_component("schema_formatting")
    assert "res_disease_name" in schema_formatting, "schema_formatting missing res_disease_name"
    print("✅ schema_formatting.txt loaded successfully")
    print(f"   Length: {len(schema_formatting)} characters")

    print()
    return True


def test_tab1_prompt():
    """Test Tab 1 (Report Generation) prompt assembly"""
    print("=" * 60)
    print("TEST 3: Tab 1 - Report Generation Prompt")
    print("=" * 60)

    loader = PromptLoader()

    prompt = loader.load_report_generation_prompt(
        user_query="고혈압 환자 대상 임상시험 타당성 분석",
        recipe_list="- get_patient_count_by_disease_keyword: 환자 수 조회\n- get_demographic_distribution_by_disease: 인구통계 분포",
        schema_info="basic_treatment, insured_person, prescribed_drug 테이블 사용 가능",
        mandatory_recipes=None
    )

    # Verify key sections
    checks = [
        ("System role (제약회사)", "제약회사" in prompt),
        ("User query", "고혈압 환자 대상 임상시험 타당성 분석" in prompt),
        ("Recipe list", "get_patient_count_by_disease_keyword" in prompt),
        ("Databricks rules", "TO_DATE" in prompt),
        ("Output validation", "JSON" in prompt),
        ("Examples", "예시" in prompt or "Example" in prompt),
    ]

    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        all_passed = all_passed and result

    print(f"\n📊 Prompt length: {len(prompt)} characters (~{len(prompt.split())} words)")
    print(f"📊 Estimated tokens: ~{len(prompt) // 4}")

    if all_passed:
        print("✅ Tab 1 prompt assembled correctly\n")
    else:
        print("❌ Tab 1 prompt has issues\n")

    return all_passed


def test_tab2_prompt():
    """Test Tab 2 (Recipe Recommendation) prompt assembly"""
    print("=" * 60)
    print("TEST 4: Tab 2 - Recipe Recommendation Prompt")
    print("=" * 60)

    loader = PromptLoader()

    prompt = loader.load_recipe_recommendation_prompt(
        disease_name="당뇨병",
        recipe_list="- analyze_treatment_duration_by_disease: 치료 기간 분석\n- analyze_medication_adherence: 약물 순응도",
        schema_info="basic_treatment, prescribed_drug 테이블 사용 가능",
        target_count=7
    )

    checks = [
        ("System role (임상 데이터 분석)", "임상 데이터 분석" in prompt),
        ("Disease name", "당뇨병" in prompt),
        ("Target count", "7개" in prompt),
        ("Recipe list", "analyze_treatment_duration_by_disease" in prompt),
        ("Output format", "recommended_recipes" in prompt),
        ("Validation rules", "JSON" in prompt),
    ]

    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        all_passed = all_passed and result

    print(f"\n📊 Prompt length: {len(prompt)} characters (~{len(prompt.split())} words)")
    print(f"📊 Estimated tokens: ~{len(prompt) // 4}")

    if all_passed:
        print("✅ Tab 2 prompt assembled correctly\n")
    else:
        print("❌ Tab 2 prompt has issues\n")

    return all_passed


def test_tab3_prompt():
    """Test Tab 3 (NL2SQL) prompt assembly"""
    print("=" * 60)
    print("TEST 5: Tab 3 - NL2SQL Prompt")
    print("=" * 60)

    loader = PromptLoader()

    prompt = loader.load_nl2sql_prompt(
        user_query="고혈압 환자의 연령대별 분포를 알려줘",
        schema_context="basic_treatment, insured_person 테이블 사용 가능"
    )

    checks = [
        ("System role (Databricks SQL)", "Databricks" in prompt),
        ("User query", "고혈압 환자의 연령대별 분포" in prompt),
        ("Schema context", "basic_treatment" in prompt),
        ("Databricks rules", "TO_DATE" in prompt),
        ("Few-shot examples", "예시" in prompt),
        ("Checklist", "체크리스트" in prompt or "checklist" in prompt.lower()),
        ("Output format", "analysis" in prompt and "sql" in prompt and "explanation" in prompt),
    ]

    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        all_passed = all_passed and result

    print(f"\n📊 Prompt length: {len(prompt)} characters (~{len(prompt.split())} words)")
    print(f"📊 Estimated tokens: ~{len(prompt) // 4}")

    if all_passed:
        print("✅ Tab 3 prompt assembled correctly\n")
    else:
        print("❌ Tab 3 prompt has issues\n")

    return all_passed


def test_examples_loading():
    """Test loading and parsing example files"""
    print("=" * 60)
    print("TEST 6: Examples Loading")
    print("=" * 60)

    loader = PromptLoader()

    # Tab 1 examples
    tab1_examples = loader.get_few_shot_examples("report_generation")
    print(f"✅ Tab 1 examples: {len(tab1_examples)} loaded")
    for i, ex in enumerate(tab1_examples, 1):
        print(f"   {i}. Type: {ex.get('type', 'unknown')}")

    # Tab 3 examples
    tab3_examples = loader.get_few_shot_examples("nl2sql")
    print(f"✅ Tab 3 examples: {len(tab3_examples)} loaded")
    for i, ex in enumerate(tab3_examples, 1):
        question = ex.get('question', 'unknown')[:50]
        print(f"   {i}. {question}...")

    print()
    return True


def test_cache_clearing():
    """Test cache mechanism"""
    print("=" * 60)
    print("TEST 7: Cache Clearing")
    print("=" * 60)

    loader = PromptLoader()

    # Load component (populates cache)
    loader._get_shared_component("databricks_rules")
    cache_size_before = len(loader._shared_cache)
    print(f"✅ Cache populated: {cache_size_before} items")

    # Clear cache
    loader.clear_cache()
    cache_size_after = len(loader._shared_cache)
    print(f"✅ Cache cleared: {cache_size_after} items")

    assert cache_size_before > 0, "Cache should be populated"
    assert cache_size_after == 0, "Cache should be empty after clearing"

    print()
    return True


def test_mandatory_recipes():
    """Test mandatory recipes injection"""
    print("=" * 60)
    print("TEST 8: Mandatory Recipes")
    print("=" * 60)

    loader = PromptLoader()

    # Without mandatory recipes
    prompt_without = loader.load_report_generation_prompt(
        user_query="Test query",
        recipe_list="Recipe 1",
        schema_info="Schema",
        mandatory_recipes=None
    )

    # With mandatory recipes
    prompt_with = loader.load_report_generation_prompt(
        user_query="Test query",
        recipe_list="Recipe 1",
        schema_info="Schema",
        mandatory_recipes="Recipe A\nRecipe B"
    )

    has_recipe_a = "Recipe A" in prompt_with
    has_recipe_b = "Recipe B" in prompt_with
    not_in_without = "Recipe A" not in prompt_without

    print(f"{'✅' if has_recipe_a else '❌'} Recipe A in prompt with mandatory")
    print(f"{'✅' if has_recipe_b else '❌'} Recipe B in prompt with mandatory")
    print(f"{'✅' if not_in_without else '❌'} Recipe A not in prompt without mandatory")

    print()
    return has_recipe_a and has_recipe_b and not_in_without


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PROMPT LOADER TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        test_file_structure,
        test_shared_components,
        test_tab1_prompt,
        test_tab2_prompt,
        test_tab3_prompt,
        test_examples_loading,
        test_cache_clearing,
        test_mandatory_recipes,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"❌ ERROR in {test_func.__name__}: {e}\n")
            results.append((test_func.__name__, False))

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Prompt system is ready to use.\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.\n")
        return 1


if __name__ == "__main__":
    exit(main())
