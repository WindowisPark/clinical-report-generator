-- Generated from: analyze_seasonal_patterns_by_disease.yaml
-- Parameters used: {'disease_name_keyword': '당뇨병', 'start_date': '2022-01-01', 'end_date': '2024-12-31', 'snapshot_dt': '2025-09-01'}

-- 특정 질환의 계절별 패턴 분석
-- 파라미터: disease_code_prefix = , start_date = 2022-01-01, end_date = 2024-12-31

SELECT
    '4. 계절별 패턴' as analysis_type,
    CASE
        WHEN MONTH(bt.created_at) IN (3,4,5) THEN '봄'
        WHEN MONTH(bt.created_at) IN (6,7,8) THEN '여름'
        WHEN MONTH(bt.created_at) IN (9,10,11) THEN '가을'
        WHEN MONTH(bt.created_at) IN (12,1,2) THEN '겨울'
    END as season,
    COUNT(DISTINCT bt.user_id) as unique_patients,
    COUNT(*) as total_treatments,
    ROUND(AVG(CAST(REGEXP_REPLACE(bt.res_total_amount, '[^0-9]', '') AS DECIMAL)), 0) as avg_cost
FROM basic_treatment bt
JOIN user u ON bt.user_id = u.id
WHERE res_disease_name LIKE '%당뇨병%'
    AND bt.created_at >= '2022-01-01'
    AND bt.created_at <= '2024-12-31'
    AND bt.deleted = false
    AND u.birthday IS NOT NULL
    AND LENGTH(u.birthday) >= 4
    AND bt.res_total_amount IS NOT NULL
GROUP BY season
ORDER BY unique_patients DESC;