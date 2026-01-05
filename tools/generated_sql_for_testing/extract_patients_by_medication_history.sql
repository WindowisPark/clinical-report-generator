-- Generated from: extract_patients_by_medication_history.yaml
-- Parameters used: {'medication_keyword': '당뇨병', 'min_prescription_days': 10, 'start_date': '2022-01-01', 'end_date': '2024-12-31', 'snapshot_dt': '2025-09-01'}

-- 특정 약물을 일정 기간 이상 복용한 환자 리스트 추출
-- 파라미터: medication_keyword = 당뇨병, min_prescription_days = 10

SELECT
  u.id as user_id,
  CONCAT(LEFT(ip.name, 1), '**') as masked_name,
  CONCAT(LEFT(ip.birthday, 4), '-**-**') as masked_birthday,
  CONCAT('***-****-', RIGHT(u.phone_number, 4)) as masked_phone,
  COUNT(DISTINCT pd.res_treat_start_date) as prescription_days,
  COLLECT_SET(pd.res_drug_name) as drug_names,
  COLLECT_SET(pd.res_ingredients) as ingredients,
  MIN(pd.res_treat_start_date) as first_prescription_date,
  MAX(pd.res_treat_start_date) as last_prescription_date
FROM prescribed_drug pd
LEFT JOIN user u ON pd.user_id = u.id
LEFT JOIN insured_person ip ON ip.user_id = u.id
WHERE pd.deleted = FALSE
  AND (pd.res_drug_name LIKE '%당뇨병%' OR pd.res_ingredients LIKE '%당뇨병%')
  AND pd.res_treat_start_date >= '2022-01-01'
  AND pd.res_treat_start_date <= '2024-12-31'
GROUP BY u.id, ip.name, ip.birthday, u.phone_number
HAVING COUNT(DISTINCT pd.res_treat_start_date) >= 10
ORDER BY prescription_days DESC
LIMIT 10000;