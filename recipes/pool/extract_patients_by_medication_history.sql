-- 특정 약물을 일정 기간 이상 복용한 환자 리스트 추출
-- 파라미터: medication_keyword = {{ medication_keyword }}, min_prescription_days = {{ min_prescription_days }}

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
  AND (pd.res_drug_name LIKE '%{{ medication_keyword }}%' OR pd.res_ingredients LIKE '%{{ medication_keyword }}%')
  AND pd.res_treat_start_date >= '{{ start_date }}'
  AND pd.res_treat_start_date <= '{{ end_date }}'
GROUP BY u.id, ip.name, ip.birthday, u.phone_number
HAVING COUNT(DISTINCT pd.res_treat_start_date) >= {{ min_prescription_days }}
ORDER BY prescription_days DESC
LIMIT 10000;