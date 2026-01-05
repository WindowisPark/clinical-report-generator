-- 스크리닝된 임상시험 대상 환자의 지역 분포 분석 (병원 주소 기준)
-- 파라미터: screening_conditions = {{ screening_conditions }}

WITH screened_patients AS (
    -- 동일한 스크리닝 로직 적용
    SELECT DISTINCT
        bt.user_id,
        bt.res_hospital_name,
        h.sido_name,
        h.sigungu_name,
        h.full_address
    FROM basic_treatment bt
    LEFT JOIN insured_person ip ON bt.user_id = ip.user_id
    LEFT JOIN hospital h ON bt.res_hospital_code = h.hospital_code
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
),

regional_summary AS (
    SELECT
        COALESCE(sido_name, '미상') AS region_name,
        COUNT(DISTINCT user_id) AS patient_count,
        COUNT(DISTINCT res_hospital_name) AS hospital_count
    FROM screened_patients
    GROUP BY sido_name
)

SELECT
    region_name,
    patient_count,
    hospital_count,
    ROUND(patient_count * 100.0 / (SELECT SUM(patient_count) FROM regional_summary), 1) AS percentage
FROM regional_summary
ORDER BY patient_count DESC
LIMIT 10;