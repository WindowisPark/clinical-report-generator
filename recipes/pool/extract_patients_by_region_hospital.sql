-- 특정 지역과 병원급별 조건에 맞는 환자 리스트 추출
-- 파라미터: region_keyword = {{ region_keyword }}, hospital_tier = {{ hospital_tier }}, min_visits = {{ min_visits }}

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
  AND h.full_address LIKE '%{{ region_keyword }}%'
  AND CASE
    WHEN h.medical_facility_type_code IN ('01','1') THEN '3차'
    WHEN h.medical_facility_type_code IN ('11','21','28','29','41','92') THEN '2차'
    ELSE '1차'
  END = '{{ hospital_tier }}'
  AND bt.res_treat_start_date >= '{{ start_date }}'
GROUP BY u.id, ip.name, ip.birthday, bt.res_hospital_name, h.full_address, hospital_grade, u.phone_number
HAVING visit_count >= {{ min_visits }}
ORDER BY visit_count DESC
LIMIT 10000;