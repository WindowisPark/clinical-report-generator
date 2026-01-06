
import pytest
import yaml
import sqlparse
import os
from core.sql_template_engine import SQLTemplateEngine

# --- Helper functions ---

def get_sql_from_file(sql_file_path):
    """Get the SQL query content from a SQL file."""
    try:
        with open(sql_file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        pytest.fail(f"SQL file not found at {sql_file_path}")
    except Exception as e:
        pytest.fail(f"An error occurred while reading {sql_file_path}: {e}")

# Initialize SQLTemplateEngine for use in tests
template_engine = SQLTemplateEngine()

# --- Test Cases ---

def test_extract_patients_by_age_gender():
    """
    Tests the 'extract_patients_by_age_gender' recipe.
    - Verifies that the SQL is generated correctly based on parameters.
    - Validates the syntax of the generated SQL.
    """
    # 1. Define test setup
    recipe_name = "extract_patients_by_age_gender"
    base_path = os.path.join("recipes", "pool")
    sql_file_path = os.path.join(base_path, f"{recipe_name}.sql")
    
    params = {
        "min_age": 30,
        "max_age": 40,
        "min_visits": 2,
        "snapshot_dt": "2023-10-01"
    }

    # 2. Load SQL template
    sql_template = get_sql_from_file(sql_file_path)

    # 3. Generate SQL
    generated_sql = template_engine.render(sql_template, params)

    # 4. Define expected SQL
    expected_sql = """-- 특정 연령대와 성별 조건에 맞는 환자 기본 정보 추출
-- 파라미터: min_age = 30, max_age = 40, min_visits = 2

SELECT
  u.id as user_id,
  CONCAT(LEFT(ip.name, 1), '**') as masked_name,
  CONCAT(LEFT(ip.birthday, 4), '-**-**') as masked_birthday,
  YEAR(CURRENT_DATE()) - TRY_CAST(LEFT(ip.birthday, 4) AS INT) as age,
  CASE
    WHEN LENGTH(ip.birthday) >= 7 AND TRY_CAST(SUBSTR(ip.birthday, 7, 1) AS INT) % 2 = 1 THEN '남성'
    WHEN LENGTH(ip.birthday) >= 7 AND TRY_CAST(SUBSTR(ip.birthday, 7, 1) AS INT) % 2 = 0 THEN '여성'
    ELSE '미상'
  END as gender,
  CONCAT('***-****-', RIGHT(u.phone_number, 4)) as masked_phone,
  COUNT(DISTINCT bt.res_treat_start_date) as total_visits,
  MIN(bt.res_treat_start_date) as first_visit_date,
  MAX(bt.res_treat_start_date) as last_visit_date
FROM user u
LEFT JOIN insured_person ip ON ip.user_id = u.id
LEFT JOIN basic_treatment bt ON bt.user_id = u.id AND bt.deleted = FALSE AND bt.snapshot_dt = '2023-10-01'
WHERE ip.birthday IS NOT NULL
  AND LENGTH(ip.birthday) = 8
  AND TRY_CAST(LEFT(ip.birthday, 4) AS INT) IS NOT NULL
  AND YEAR(CURRENT_DATE()) - TRY_CAST(LEFT(ip.birthday, 4) AS INT) BETWEEN 30 AND 40
GROUP BY u.id, ip.name, ip.birthday, u.phone_number
HAVING total_visits >= 2
ORDER BY age, last_visit_date DESC
LIMIT 10000;"""

    # 5. Assertions
    # Removing leading/trailing whitespace for robust comparison
    assert generated_sql.strip() == expected_sql.strip()

    # Validate SQL syntax
    parsed = sqlparse.parse(generated_sql)
    assert len(parsed) > 0, "SQL parsing failed."
    # Check for parsing errors (this is a basic check)
    for statement in parsed:
        # A simple check is to see if the token list contains an error token
        error_token_exists = any(t.ttype is sqlparse.tokens.Error for t in statement.flatten())
        assert not error_token_exists, f"SQL syntax error detected in statement: {statement}"


def test_get_top_prescribed_ingredients_by_disease():
    """
    Tests the 'get_top_prescribed_ingredients_by_disease' recipe.
    - Verifies correct SQL generation with date filters.
    - Validates SQL syntax.
    """
    # 1. Define test setup
    recipe_name = "get_top_prescribed_ingredients_by_disease"
    base_path = os.path.join("recipes", "profile")
    sql_file_path = os.path.join(base_path, f"{recipe_name}.sql")
    
    params = {
        "disease_name_keyword": "원형탈모증",
        "start_date": "2022-01-01",
        "end_date": "2024-12-31",
        "top_n": 7
    }

    # 2. Load SQL template
    sql_template = get_sql_from_file(sql_file_path)

    # 3. Generate SQL
    generated_sql = template_engine.render(sql_template, params)

    # 4. Define expected SQL
    expected_sql = """-- 특정 질환을 가진 환자들에게 가장 많이 처방된 약물 성분 Top N 집계
-- 파라미터: disease_name_keyword = 원형탈모증, start_date = 2022-01-01, end_date = 2024-12-31, top_n = 7

SELECT
    pd.res_ingredients,
    COUNT(*) AS prescription_count
FROM basic_treatment bt
JOIN hospital_info hi
    ON bt.res_hospital_code = hi.hospital_code
JOIN prescribed_drug pd
    ON bt.user_id = pd.user_id
    AND bt.res_treat_start_date = pd.res_treat_start_date
WHERE bt.deleted = FALSE
    AND pd.deleted = FALSE
    AND bt.res_disease_name LIKE '%원형탈모증%'
    AND bt.res_treat_start_date BETWEEN '2022-01-01' AND '2024-12-31'
GROUP BY pd.res_ingredients
ORDER BY prescription_count DESC
LIMIT 7;"""

    # 5. Assertions
    assert generated_sql.strip() == expected_sql.strip()

    parsed = sqlparse.parse(generated_sql)
    assert len(parsed) > 0, "SQL parsing failed."
    for statement in parsed:
        error_token_exists = any(t.ttype is sqlparse.tokens.Error for t in statement.flatten())
        assert not error_token_exists, f"SQL syntax error detected in statement: {statement}"

