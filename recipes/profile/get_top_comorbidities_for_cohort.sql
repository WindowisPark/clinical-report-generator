WITH target_patients AS (
    SELECT DISTINCT bt.user_id
    FROM basic_treatment bt
    JOIN user u ON bt.user_id = u.id
    WHERE bt.res_disease_name LIKE '%{{ disease_name_keyword }}%' -- 파라미터 1
        AND bt.res_treat_start_date >= '{{ start_date }}'     -- 파라미터 2 (통일: res_treat_start_date)
        AND bt.res_treat_start_date <= '{{ end_date }}'       -- 파라미터 3 (통일: res_treat_start_date)
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
    WHERE bt2.res_disease_name NOT LIKE '%{{ disease_name_keyword }}%' -- 주 질환 제외
        AND bt2.deleted = false
        AND bt2.res_treat_start_date >= '{{ start_date }}' -- 주 질환과 동일 기간 적용 (통일: res_treat_start_date)
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
HAVING COUNT(DISTINCT user_id) >= {{ min_patient_count | default(10) }} -- 파라미터 4
ORDER BY patients_with_comorbidity DESC
LIMIT {{ top_n | default(10) }}; -- 파라미터 5