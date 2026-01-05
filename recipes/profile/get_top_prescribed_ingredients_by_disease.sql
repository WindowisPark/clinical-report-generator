-- 특정 질환을 가진 환자들에게 가장 많이 처방된 약물 성분 Top N 집계
-- 파라미터: disease_name_keyword = {{ disease_name_keyword }}, start_date = {{ start_date }}, end_date = {{ end_date }}, top_n = {{ top_n }}

SELECT
    pd.res_ingredients,
    COUNT(*) AS prescription_count
FROM basic_treatment bt
JOIN prescribed_drug pd
    ON bt.user_id = pd.user_id
    AND bt.res_treat_start_date = pd.res_treat_start_date
WHERE bt.deleted = FALSE
    AND pd.deleted = FALSE
    AND bt.res_disease_name LIKE '%{{ disease_name_keyword }}%'
    AND bt.res_treat_start_date BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY pd.res_ingredients
ORDER BY prescription_count DESC
LIMIT {{ top_n | default(10) }};