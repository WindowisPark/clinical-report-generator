-- Generated from: analyze_overall_drug_topn.yaml
-- Parameters used: {'disease_keyword': '당뇨병', 'start_date': '2022-01-01', 'end_date': '2024-12-31', 'min_patients': 50, 'top_n': 30, 'snapshot_dt': '2025-09-01'}

-- 특정 질환에서 처방되는 약물 TOP N (처방량 기준)
-- 파라미터: disease_keyword = 당뇨병, min_patients = 50, top_n = 30

WITH disease_patients AS (
  SELECT DISTINCT user_id
  FROM basic_treatment
  WHERE deleted = FALSE
    AND LOWER(res_disease_name) LIKE LOWER('%당뇨병%')
    AND res_treat_start_date >= '2022-01-01'
    AND res_treat_start_date <= '2024-12-31'
),
disease_prescriptions AS (
  SELECT
    pd.res_ingredients as drug_ingredient,
    pd.user_id,
    pd.res_treat_start_date,
    bt.res_disease_name
  FROM prescribed_drug pd
  INNER JOIN disease_patients dp ON pd.user_id = dp.user_id
  LEFT JOIN basic_treatment bt ON pd.user_id = bt.user_id AND pd.res_treat_start_date = bt.res_treat_start_date
  WHERE pd.deleted = FALSE
    AND pd.res_treat_start_date >= '2022-01-01'
    AND pd.res_treat_start_date <= '2024-12-31'
    AND pd.res_ingredients IS NOT NULL
),
drug_stats AS (
  SELECT
    drug_ingredient,
    COUNT(DISTINCT user_id) as unique_patients,
    COUNT(DISTINCT res_treat_start_date) as total_prescriptions,
    COUNT(DISTINCT res_disease_name) as indicated_diseases,
    COLLECT_SET(res_disease_name) as all_diseases
  FROM disease_prescriptions
  GROUP BY drug_ingredient
)
SELECT
  drug_ingredient,
  unique_patients,
  total_prescriptions,
  indicated_diseases,
  all_diseases,
  ROUND(unique_patients * 100.0 / (SELECT COUNT(DISTINCT user_id) FROM disease_patients), 2) as prescription_rate_pct
FROM drug_stats
WHERE unique_patients >= 50
ORDER BY unique_patients DESC, total_prescriptions DESC
LIMIT 30;