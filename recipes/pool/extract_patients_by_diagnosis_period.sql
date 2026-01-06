-- 특정 질환의 진단 기간을 기준으로 신규환자와 기존환자 구분 추출
-- 파라미터: disease_keyword = {{ disease_keyword }}, cutoff_date = {{ cutoff_date }}, min_visits = {{ min_visits }}

SELECT
  u.id as user_id,
  CONCAT(LEFT(ip.name, 1), '**') as masked_name,
  CONCAT(LEFT(ip.birthday, 4), '-**-**') as masked_birthday,
  MIN(bt.res_treat_start_date) as first_diagnosis_date,
  MAX(bt.res_treat_start_date) as last_visit_date,
  COUNT(DISTINCT bt.res_treat_start_date) as total_visits,
  CASE
    WHEN MIN(bt.res_treat_start_date) >= '{{ cutoff_date }}' THEN '신규환자'
    ELSE '기존환자'
  END as patient_type,
  CONCAT('***-****-', RIGHT(u.phone_number, 4)) as masked_phone,
  COLLECT_SET(bt.res_disease_name) as disease_list
FROM basic_treatment bt
LEFT JOIN user u ON bt.user_id = u.id
LEFT JOIN insured_person ip ON ip.user_id = bt.user_id
WHERE bt.deleted = FALSE
  AND bt.res_disease_name LIKE '%{{ disease_keyword }}%'
  AND bt.res_treat_start_date >= '{{ start_date }}'
GROUP BY u.id, ip.name, ip.birthday, u.phone_number
HAVING total_visits >= {{ min_visits }}
ORDER BY first_diagnosis_date DESC
LIMIT 10000;