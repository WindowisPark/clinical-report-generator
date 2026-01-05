-- Generated from: extract_patients_with_complications.yaml
-- Parameters used: {'main_disease_keyword': '당뇨병', 'complication_keywords': '당뇨병', 'start_date': '2022-01-01', 'min_main_visits': 1, 'min_complication_visits': 1, 'snapshot_dt': '2025-09-01'}

-- 주 질환과 합병증을 모두 가진 환자 추출
-- 파라미터: main_disease_keyword = 당뇨병, complication_keywords = 당뇨병

SELECT
  u.id as user_id,
  CONCAT(LEFT(ip.name, 1), '**') as masked_name,
  CONCAT(LEFT(ip.birthday, 4), '-**-**') as masked_birthday,
  COUNT(DISTINCT CASE WHEN bt.res_disease_name LIKE '%당뇨병%' THEN bt.res_treat_start_date END) as main_disease_visits,
  COUNT(DISTINCT CASE WHEN REGEXP_LIKE(bt.res_disease_name, '당뇨병') THEN bt.res_treat_start_date END) as complication_visits,
  COLLECT_SET(CASE WHEN REGEXP_LIKE(bt.res_disease_name, '당뇨병') THEN bt.res_disease_name END) as complications,
  MIN(bt.res_treat_start_date) as first_visit,
  MAX(bt.res_treat_start_date) as last_visit,
  CONCAT('***-****-', RIGHT(u.phone_number, 4)) as masked_phone
FROM basic_treatment bt
LEFT JOIN user u ON bt.user_id = u.id
LEFT JOIN insured_person ip ON ip.user_id = bt.user_id
WHERE bt.deleted = FALSE
  AND bt.res_treat_start_date >= '2022-01-01'
GROUP BY u.id, ip.name, ip.birthday, u.phone_number
HAVING main_disease_visits >= 1 AND complication_visits >= 1
ORDER BY complication_visits DESC, main_disease_visits DESC
LIMIT 10000;