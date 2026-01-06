-- 스크리닝된 임상시험 대상 환자의 성별 분포 분석
-- 파라미터: screening_conditions = {{ screening_conditions }}

WITH screened_patients AS (
    -- 동일한 스크리닝 로직 적용
    SELECT DISTINCT
        bt.user_id,
        ip.gender
    FROM basic_treatment bt
    LEFT JOIN insured_person ip ON bt.user_id = ip.user_id
    WHERE bt.deleted = FALSE
      AND bt.res_treat_start_date >= '{{ start_date }}'
      AND bt.res_treat_start_date <= '{{ end_date }}'
      AND bt.res_disease_name LIKE '%{{ disease_name_keyword }}%'
      -- 제외 조건 적용
      AND NOT EXISTS (
          SELECT 1 FROM basic_treatment bt2
          WHERE bt2.user_id = bt.user_id
            AND bt2.deleted = FALSE
            AND (
                bt2.res_disease_name LIKE '%악성%' OR
                bt2.res_disease_name LIKE '%종양%' OR
                bt2.res_disease_name LIKE '%암%' OR
                bt2.res_disease_name LIKE '%심근경색%' OR
                bt2.res_disease_name LIKE '%뇌졸중%'
            )
      )
)

SELECT
    CASE
        WHEN gender = 'MAN' THEN '남성'
        WHEN gender = 'WOMAN' THEN '여성'
        ELSE '미상'
    END AS gender_description,
    COUNT(DISTINCT user_id) AS patient_count,
    ROUND(COUNT(DISTINCT user_id) * 100.0 / (SELECT COUNT(DISTINCT user_id) FROM screened_patients), 1) AS percentage
FROM screened_patients
GROUP BY gender
ORDER BY patient_count DESC;