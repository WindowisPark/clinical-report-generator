-- Generated from: analyze_main_hospital_tier_for_co_prescription.yaml
-- Parameters used: {'disease_keyword': '당뇨병', 'drug1_keyword': '당뇨병', 'drug2_keyword': '당뇨병', 'snapshot_dt': '2025-09-01'}

WITH base_visits AS (
  SELECT DISTINCT
    pd.user_id,
    pd.res_treat_start_date,
    pd.res_hospital_name
  FROM prescribed_drug pd
  JOIN basic_treatment bt
    ON pd.user_id = bt.user_id AND pd.res_treat_start_date = bt.res_treat_start_date
  WHERE bt.res_disease_name LIKE '%' || '당뇨병' || '%' -- 파라미터 1
),

drug_flags AS (
  SELECT
    user_id,
    res_treat_start_date,
    MAX(CASE WHEN LOWER(res_ingredients) LIKE '%' || lower('당뇨병') || '%' THEN 1 ELSE 0 END) AS has_drug1, -- 파라미터 2
    MAX(CASE WHEN LOWER(res_ingredients) LIKE '%' || lower('당뇨병') || '%' THEN 1 ELSE 0 END) AS has_drug2  -- 파라미터 3
  FROM prescribed_drug
  GROUP BY user_id, res_treat_start_date
),

merged AS (
  SELECT
    b.user_id,
    b.res_treat_start_date,
    b.res_hospital_name
  FROM base_visits b
  JOIN drug_flags d
    ON b.user_id = d.user_id AND b.res_treat_start_date = d.res_treat_start_date
  WHERE d.has_drug1 = 1 AND d.has_drug2 = 1
),

hospital_grade_raw AS (
  SELECT
    m.user_id,
    m.res_hospital_name,
    CASE
      WHEN SUBSTRING(bt.res_hospital_code, 3, 1) = '1' THEN '3차'
      WHEN SUBSTRING(bt.res_hospital_code, 3, 1) = '2' THEN '2차'
      WHEN SUBSTRING(bt.res_hospital_code, 3, 1) = '3' THEN '1차'
      ELSE '기타'
    END AS hospital_level
  FROM merged m
  JOIN basic_treatment bt
    ON m.user_id = bt.user_id AND m.res_treat_start_date = bt.res_treat_start_date
  WHERE bt.deleted = FALSE
    AND bt.res_hospital_code IS NOT NULL
),

ranked_hospital AS (
  SELECT
    user_id,
    hospital_level,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY COUNT(*) DESC) AS rn
  FROM hospital_grade_raw
  GROUP BY user_id, hospital_level
)

SELECT
  hospital_level,
  COUNT(*) AS unique_patient_count
FROM ranked_hospital
WHERE rn = 1
GROUP BY hospital_level
ORDER BY hospital_level;