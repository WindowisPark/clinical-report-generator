-- 특정 키워드가 포함된 질환명을 가진 환자 수를 질환별로 집계
-- 파라미터: disease_keyword = {{ disease_keyword }}

SELECT
    res_disease_name,
    COUNT(DISTINCT user_id) AS unique_patient_count
FROM basic_treatment
WHERE res_disease_name LIKE '%{{ disease_keyword }}%'
    AND deleted = FALSE
GROUP BY res_disease_name
ORDER BY unique_patient_count DESC
LIMIT 10000;