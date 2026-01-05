-- 특정 연령대와 성별 조건에 맞는 환자 기본 정보 추출
-- 파라미터: min_age = {{ min_age }}, max_age = {{ max_age }}, min_visits = {{ min_visits }}

SELECT
  u.id as user_id,
  CONCAT(LEFT(ip.name, 1), '**') as masked_name,
  CONCAT(LEFT(ip.birthday, 4), '-**-**') as masked_birthday,
  YEAR(CURRENT_DATE()) - TRY_CAST(LEFT(ip.birthday, 4) AS INTEGER) as age,
  CASE
    WHEN LENGTH(ip.birthday) >= 7 AND TRY_CAST(SUBSTR(ip.birthday, 7, 1) AS INTEGER) % 2 = 1 THEN '남성'
    WHEN LENGTH(ip.birthday) >= 7 AND TRY_CAST(SUBSTR(ip.birthday, 7, 1) AS INTEGER) % 2 = 0 THEN '여성'
    ELSE '미상'
  END as gender,
  CONCAT('***-****-', RIGHT(u.phone_number, 4)) as masked_phone,
  COUNT(DISTINCT bt.res_treat_start_date) as total_visits,
  MIN(bt.res_treat_start_date) as first_visit_date,
  MAX(bt.res_treat_start_date) as last_visit_date
FROM user u
LEFT JOIN insured_person ip ON ip.user_id = u.id
LEFT JOIN basic_treatment bt ON bt.user_id = u.id AND bt.deleted = FALSE
WHERE ip.birthday IS NOT NULL
  AND LENGTH(ip.birthday) = 8
  AND TRY_CAST(LEFT(ip.birthday, 4) AS INTEGER) IS NOT NULL
  AND YEAR(CURRENT_DATE()) - TRY_CAST(LEFT(ip.birthday, 4) AS INTEGER) BETWEEN {{ min_age }} AND {{ max_age }}
GROUP BY u.id, ip.name, ip.birthday, u.phone_number
HAVING total_visits >= {{ min_visits }}
ORDER BY age, last_visit_date DESC
LIMIT 10000;