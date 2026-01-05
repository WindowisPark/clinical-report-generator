-- Generated from: get_top_comorbidities_for_cohort.yaml
-- Parameters used: {'disease_name_keyword': '당뇨병', 'start_date': '2022-01-01', 'end_date': '2024-12-31', 'min_patient_count': 50, 'top_n': 10, 'snapshot_dt': '2025-09-01'}

WITH target_patients AS (
    SELECT DISTINCT bt.user_id
    FROM basic_treatment bt
    JOIN user u ON bt.user_id = u.id
    WHERE bt.res_disease_name LIKE '%당뇨병%' -- 파라미터 1
        AND bt.created_at >= '2022-01-01'               -- 파라미터 2
        AND bt.created_at <= '2024-12-31'                 -- 파라미터 3
        AND bt.deleted = false
        AND u.birthday IS NOT NULL
        AND LENGTH(u.birthday) >= 4
),
comorbidities AS (
    SELECT
        tp.user_id,
        bt2.res_disease_code as comorbid_code,
        bt2.res_disease_name as comorbid_name,
        COUNT(*) as comorbid_frequency
    FROM target_patients tp
    JOIN basic_treatment bt2 ON tp.user_id = bt2.user_id
    WHERE bt2.res_disease_name NOT LIKE '%당뇨병%' -- 주 질환 제외
        AND bt2.deleted = false
        AND bt2.created_at >= '2022-01-01' -- 주 질환과 동일 기간 적용
        AND bt2.res_disease_code IS NOT NULL
        AND bt2.res_disease_code NOT LIKE '$해당없음'
        AND bt2.res_disease_name IS NOT NULL
    GROUP BY tp.user_id, bt2.res_disease_code, bt2.res_disease_name
)

SELECT
    '3. 주요 동반질환' as analysis_type,
    comorbid_code,
    comorbid_name,
    COUNT(DISTINCT user_id) as patients_with_comorbidity,
    ROUND(COUNT(DISTINCT user_id) * 100.0 / (SELECT COUNT(DISTINCT user_id) FROM target_patients), 2) as prevalence_percentage,
    ROUND(AVG(comorbid_frequency), 1) as avg_treatments_per_patient
FROM comorbidities
GROUP BY comorbid_code, comorbid_name
HAVING patients_with_comorbidity >= 50 -- 파라미터 4
ORDER BY patients_with_comorbidity DESC
LIMIT 10; -- 파라미터 5