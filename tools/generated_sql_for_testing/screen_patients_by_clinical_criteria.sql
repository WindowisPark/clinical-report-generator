-- Generated from: screen_patients_by_clinical_criteria.yaml
-- Parameters used: {'neuropathy_keyword': '당뇨병', 'neuropathy_exclude_keyword': '당뇨병', 'exclusion_disease_keyword': '당뇨병', 'snapshot_dt': '2025-09-01'}

-- 포함/제외 기준에 따른 환자 스크리닝
WITH recent_neuropathy_patients AS (
  SELECT DISTINCT bt.user_id
  FROM `basic_treatment` bt
  WHERE bt.res_disease_name LIKE CONCAT('%', '당뇨병', '%')             -- 파라미터 1
    AND bt.res_disease_name NOT LIKE CONCAT('%', '당뇨병', '%') -- 파라미터 2
    AND TO_DATE(bt.res_treat_start_date, 'yyyyMMdd') >= DATE_ADD(CURRENT_DATE, -365)
    AND bt.deleted = FALSE
),

resection_in_6months AS (
  SELECT DISTINCT dt.user_id
  FROM `detail_treatment` dt
  WHERE dt.res_code_name LIKE '%차단술%'
    AND TO_DATE(dt.res_treat_start_date, 'yyyyMMdd') >= DATE_ADD(CURRENT_DATE, -180)
    AND dt.deleted = FALSE
),

injection_in_90days AS (
  SELECT DISTINCT dt.user_id
  FROM `detail_treatment` dt
  WHERE dt.res_code_name LIKE '%주사%'
    AND TO_DATE(dt.res_treat_start_date, 'yyyyMMdd') >= DATE_ADD(CURRENT_DATE, -90)
    AND dt.deleted = FALSE
),

diabetes_patients AS (
  SELECT DISTINCT bt.user_id
  FROM `basic_treatment` bt
  WHERE bt.res_disease_name LIKE CONCAT('%', '당뇨병', '%')  -- 파라미터 3
    AND bt.deleted = FALSE
),

last_two_visits AS (
  SELECT
    bt.user_id,
    bt.res_hospital_code,
    TO_DATE(bt.res_treat_start_date, 'yyyyMMdd') AS visit_date,
    ROW_NUMBER() OVER (PARTITION BY bt.user_id ORDER BY TO_DATE(bt.res_treat_start_date, 'yyyyMMdd') DESC, bt.basic_treatment_id DESC) AS rn
  FROM `basic_treatment` bt
  WHERE bt.deleted = FALSE
),

last_visit AS (
  SELECT ltv.user_id, h.full_address AS last_hospital_address
  FROM last_two_visits ltv
  LEFT JOIN `hospital` h ON h.hospital_code = ltv.res_hospital_code
  WHERE ltv.rn = 1
),

second_last_visit AS (
  SELECT ltv.user_id, h.full_address AS second_last_hospital_address
  FROM last_two_visits ltv
  LEFT JOIN `hospital` h ON h.hospital_code = ltv.res_hospital_code
  WHERE ltv.rn = 2
)

SELECT
  u.id AS user_id,
  CONCAT(LEFT(ip.name, 1), '**') AS masked_name,
  CONCAT('***-****-', RIGHT(u.phone_number, 4)) AS masked_phone,
  CASE WHEN rnp.user_id IS NOT NULL THEN 'O' ELSE 'X' END AS recent_neuropathy,
  CASE WHEN r6.user_id IS NOT NULL THEN 'O' ELSE 'X' END AS resection_in_6months,
  CASE WHEN i90.user_id IS NOT NULL THEN 'O' ELSE 'X' END AS injection_in_90days,
  lv.last_hospital_address,
  slv.second_last_hospital_address
FROM `user` u
LEFT JOIN `insured_person` ip ON ip.user_id = u.id
LEFT JOIN recent_neuropathy_patients rnp ON u.id = rnp.user_id
LEFT JOIN resection_in_6months r6 ON u.id = r6.user_id
LEFT JOIN injection_in_90days i90 ON u.id = i90.user_id
LEFT JOIN diabetes_patients dp ON u.id = dp.user_id
LEFT JOIN last_visit lv ON u.id = lv.user_id
LEFT JOIN second_last_visit slv ON u.id = slv.user_id
WHERE (rnp.user_id IS NOT NULL OR r6.user_id IS NOT NULL OR i90.user_id IS NOT NULL) -- 포함 기준: 셋 중 하나라도 해당
  AND dp.user_id IS NULL; -- 제외 기준: 당뇨 이력 없음