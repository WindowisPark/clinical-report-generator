-- 특정 질환의 월별 패턴 분석
-- 파라미터: disease_name_keyword = {{ disease_name_keyword }}, start_date = {{ start_date }}, end_date = {{ end_date }}

SELECT
    DATE_FORMAT(bt.res_treat_start_date, 'yyyy-MM') as year_month,
    YEAR(bt.res_treat_start_date) as year,
    MONTH(bt.res_treat_start_date) as month,
    COUNT(DISTINCT bt.user_id) as unique_patients,
    COUNT(*) as total_treatments,
    ROUND(AVG(CASE
        WHEN bt.res_total_amount IS NOT NULL
        THEN CAST(REGEXP_REPLACE(bt.res_total_amount, '[^0-9]', '') AS DECIMAL)
        ELSE NULL
    END), 0) as avg_cost_per_treatment
FROM basic_treatment bt
WHERE bt.res_disease_name LIKE '%{{ disease_name_keyword }}%'
    AND bt.res_treat_start_date >= '{{ start_date }}'
    AND bt.res_treat_start_date <= '{{ end_date }}'
    AND bt.deleted = false
GROUP BY
    DATE_FORMAT(bt.res_treat_start_date, 'yyyy-MM'),
    YEAR(bt.res_treat_start_date),
    MONTH(bt.res_treat_start_date)
ORDER BY year_month;
