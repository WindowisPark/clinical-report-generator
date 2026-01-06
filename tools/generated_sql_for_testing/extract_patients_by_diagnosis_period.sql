-- Generated from: extract_patients_by_diagnosis_period.yaml
-- Parameters used: {'disease_keyword': '당뇨병', 'cutoff_date': '2024-12-31', 'start_date': '2022-01-01', 'min_visits': 2, 'snapshot_dt': '2025-09-01'}

-- 특정 질환의 진단 기간을 기준으로 신규환자와 기존환자 구분 추출
-- 파라미터: disease_keyword = 당뇨병, cutoff_date = 2024-12-31, min_visits = 2

SELECT
  u.id as user_id,
  CONCAT(LEFT(ip.name, 1), '**') as masked_name,
  CONCAT(LEFT(ip.birthday, 4), '-**-**') as masked_birthday,
  MIN(bt.res_treat_start_date) as first_diagnosis_date,
  MAX(bt.res_treat_start_date) as last_visit_date,
  COUNT(DISTINCT bt.res_treat_start_date) as total_visits,
  CASE
    WHEN MIN(bt.res_treat_start_date) >= '2024-12-31' THEN '신규환자'
    ELSE '기존환자'
  END as patient_type,
  CONCAT('***-****-', RIGHT(u.phone_number, 4)) as masked_phone,
  COLLECT_SET(bt.res_disease_name) as disease_list
FROM basic_treatment bt
LEFT JOIN user u ON bt.user_id = u.id
LEFT JOIN insured_person ip ON ip.user_id = bt.user_id
WHERE bt.deleted = FALSE
  AND bt.res_disease_name LIKE '%당뇨병%'
  AND bt.res_treat_start_date >= '2022-01-01'
GROUP BY u.id, ip.name, ip.birthday, u.phone_number
HAVING total_visits >= 2
ORDER BY first_diagnosis_date DESC
LIMIT 10000;