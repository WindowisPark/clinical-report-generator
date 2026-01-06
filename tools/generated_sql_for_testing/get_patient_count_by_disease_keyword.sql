-- Generated from: get_patient_count_by_disease_keyword.yaml
-- Parameters used: {'disease_keyword': '당뇨병', 'snapshot_dt': '2025-09-01'}

-- 특정 키워드가 포함된 질환명을 가진 환자 수를 질환별로 집계
-- 파라미터: disease_keyword = 당뇨병

SELECT
    res_disease_name,
    COUNT(DISTINCT user_id) AS unique_patient_count
FROM basic_treatment
WHERE res_disease_name LIKE '%당뇨병%'
    AND deleted = FALSE
GROUP BY res_disease_name
ORDER BY unique_patient_count DESC
LIMIT 10000;