-- 스크리닝된 임상시험 대상 환자의 총 수 집계
-- 파라미터: screening_conditions = {{ screening_conditions }}

WITH screened_patients AS (
    -- screen_patients_by_clinical_criteria 레시피의 결과를 기반으로 한 환자 집계
    SELECT DISTINCT
        bt.user_id,
        ip.gender,
        bt.res_hospital_name,
        h.sido_name,
        h.sigungu_name
    FROM basic_treatment bt
    LEFT JOIN insured_person ip ON bt.user_id = ip.user_id
    LEFT JOIN hospital h ON bt.res_hospital_code = h.hospital_code
    WHERE bt.deleted = FALSE
      AND bt.res_treat_start_date >= '{{ start_date }}'
      AND bt.res_treat_start_date <= '{{ end_date }}'
      AND bt.res_disease_name LIKE '%{{ disease_name_keyword }}%'
      -- 제외 조건: 악성종양, 심근경색, 뇌졸중 관련 기록이 없는 환자
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
    '{{ screening_conditions }}' AS screening_description,
    COUNT(DISTINCT user_id) AS total_screened_patients,
    COUNT(DISTINCT CASE WHEN gender = 'MAN' THEN user_id END) AS male_patients,
    COUNT(DISTINCT CASE WHEN gender = 'WOMAN' THEN user_id END) AS female_patients,
    COUNT(DISTINCT sido_name) AS regions_covered,
    COUNT(DISTINCT res_hospital_name) AS hospitals_involved
FROM screened_patients;