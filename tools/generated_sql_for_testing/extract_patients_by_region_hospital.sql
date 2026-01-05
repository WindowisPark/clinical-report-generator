-- Generated from: extract_patients_by_region_hospital.yaml
-- Parameters used: {'region_keyword': '당뇨병', 'hospital_tier': 'test_string', 'min_visits': 2, 'start_date': '2022-01-01', 'snapshot_dt': '2025-09-01'}

-- 특정 지역과 병원급별 조건에 맞는 환자 리스트 추출
-- 파라미터: region_keyword = 당뇨병, hospital_tier = test_string, min_visits = 2

SELECT
  u.id as user_id,
  CONCAT(LEFT(ip.name, 1), '**') as masked_name,
  CONCAT(LEFT(ip.birthday, 4), '-**-**') as masked_birthday,
  bt.res_hospital_name,
  h.full_address,
  CASE
    WHEN h.medical_facility_type_code IN ('01','1') THEN '3차'
    WHEN h.medical_facility_type_code IN ('11','21','28','29','41','92') THEN '2차'
    ELSE '1차'
  END AS hospital_grade,
  COUNT(DISTINCT bt.res_treat_start_date) as visit_count,
  MIN(bt.res_treat_start_date) as first_visit,
  MAX(bt.res_treat_start_date) as last_visit,
  CONCAT('***-****-', RIGHT(u.phone_number, 4)) as masked_phone
FROM basic_treatment bt
LEFT JOIN user u ON bt.user_id = u.id
LEFT JOIN insured_person ip ON ip.user_id = bt.user_id
LEFT JOIN hospital h ON bt.res_hospital_code = h.hospital_code
WHERE bt.deleted = FALSE
  AND h.full_address LIKE '%당뇨병%'
  AND CASE
    WHEN h.medical_facility_type_code IN ('01','1') THEN '3차'
    WHEN h.medical_facility_type_code IN ('11','21','28','29','41','92') THEN '2차'
    ELSE '1차'
  END = 'test_string'
  AND bt.res_treat_start_date >= '2022-01-01'
GROUP BY u.id, ip.name, ip.birthday, bt.res_hospital_name, h.full_address, hospital_grade, u.phone_number
HAVING visit_count >= 2
ORDER BY visit_count DESC
LIMIT 10000;