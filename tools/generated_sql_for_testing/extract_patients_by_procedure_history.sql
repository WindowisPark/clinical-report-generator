-- Generated from: extract_patients_by_procedure_history.yaml
-- Parameters used: {'procedure_keyword': '당뇨병', 'start_date': '2022-01-01', 'end_date': '2024-12-31', 'snapshot_dt': '2025-09-01'}

-- 특정 수술/시술을 받은 환자 리스트 추출
-- 파라미터: procedure_keyword = 당뇨병

SELECT
  u.id as user_id,
  CONCAT(LEFT(ip.name, 1), '**') as masked_name,
  CONCAT(LEFT(ip.birthday, 4), '-**-**') as masked_birthday,
  bt.res_treat_start_date as procedure_date,
  bt.res_hospital_name,
  h.full_address as hospital_address,
  CASE
    WHEN h.medical_facility_type_code IN ('01','1') THEN '3차'
    WHEN h.medical_facility_type_code IN ('11','21','28','29','41','92') THEN '2차'
    ELSE '1차'
  END AS hospital_grade,
  bt.res_disease_name,
  CONCAT('***-****-', RIGHT(u.phone_number, 4)) as masked_phone
FROM basic_treatment bt
LEFT JOIN user u ON bt.user_id = u.id
LEFT JOIN insured_person ip ON ip.user_id = bt.user_id
LEFT JOIN hospital h ON bt.res_hospital_code = h.hospital_code
WHERE bt.deleted = FALSE
  AND bt.res_disease_name LIKE '%당뇨병%'
  AND bt.res_treat_start_date >= '2022-01-01'
  AND bt.res_treat_start_date <= '2024-12-31'
ORDER BY bt.res_treat_start_date DESC
LIMIT 10000;