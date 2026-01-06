-- Generated from: get_top_prescribed_ingredients_by_disease.yaml
-- Parameters used: {'disease_name_keyword': '당뇨병', 'start_date': '2022-01-01', 'end_date': '2024-12-31', 'top_n': 10, 'snapshot_dt': '2025-09-01'}

-- 특정 질환을 가진 환자들에게 가장 많이 처방된 약물 성분 Top N 집계
-- 파라미터: disease_name_keyword = 당뇨병, start_date = 2022-01-01, end_date = 2024-12-31, top_n = 10

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
    AND bt.res_disease_name LIKE '%당뇨병%'
    AND bt.res_treat_start_date BETWEEN '2022-01-01' AND '2024-12-31'
GROUP BY pd.res_ingredients
ORDER BY prescription_count DESC
LIMIT 10;