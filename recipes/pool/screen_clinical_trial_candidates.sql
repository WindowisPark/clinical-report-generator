-- 임상시험 후보자 선정을 위한 복잡한 스크리닝 (연령, 지역, 상세 제외 기준 적용)
-- 파라미터: exclusion_window_months = {{ exclusion_window_months }}, min_age = {{ min_age }}, max_age = {{ max_age }}
WITH params AS (
  SELECT
    {{ exclusion_window_months }} AS ex_window_months,                                -- 파라미터 1: 배제 조건 기간(개월)
    DATE_SUB(CURRENT_DATE, {{ exclusion_window_months }} * 30) AS dt_ex_window
),

-- ========== 기본 진료데이터(정규화) ==========
bt AS (
  SELECT
    CAST(bt.user_id AS STRING) AS user_id,
    CASE WHEN CAST(bt.res_treat_start_date AS STRING) RLIKE '^[0-9]{8}$' THEN TO_DATE(CAST(bt.res_treat_start_date AS STRING), 'yyyyMMdd') ELSE NULL END AS treat_date,
    UPPER(COALESCE(bt.res_disease_name, ''))  AS disease_name,
    UPPER(COALESCE(bt.res_disease_code, ''))  AS disease_code,
    TRIM(CAST(bt.res_hospital_code AS STRING)) AS hospital_code
  FROM basic_treatment bt
  WHERE bt.deleted = FALSE
),

pd AS (
  SELECT
    CAST(pd.user_id AS STRING) AS user_id,
    UPPER(COALESCE(pd.res_drug_name, ''))    AS drug_name,
    UPPER(COALESCE(pd.res_ingredients, '')) AS ingredients,
    CASE WHEN CAST(pd.res_treat_start_date AS STRING) RLIKE '^[0-9]{8}$' THEN TO_DATE(CAST(pd.res_treat_start_date AS STRING), 'yyyyMMdd') ELSE NULL END AS treat_date
  FROM prescribed_drug pd
),
dt AS (
  SELECT
    CAST(d.user_id AS STRING) AS user_id,
    UPPER(COALESCE(d.res_code_name, ''))  AS code_name,
    UPPER(COALESCE(d.res_treat_type, '')) AS treat_type,
    CASE WHEN CAST(d.res_treat_start_date AS STRING) RLIKE '^[0-9]{8}$' THEN TO_DATE(CAST(d.res_treat_start_date AS STRING), 'yyyyMMdd') ELSE NULL END AS treat_date
  FROM detail_treatment d
),

-- ========== 최근 3회 중 서울/경기/인천 1회 이상 ==========
bt_loc AS (
  SELECT b.user_id, b.treat_date, COALESCE(h.sido_name, NULL) AS sido_name
  FROM bt b
  LEFT JOIN hospital h ON TRIM(CAST(h.hospital_code AS STRING)) = b.hospital_code
  WHERE b.treat_date IS NOT NULL
),
ranked_visits AS (
  SELECT user_id, treat_date, sido_name, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY treat_date DESC) AS rn
  FROM bt_loc
),
last3 AS (
  SELECT user_id, treat_date, sido_name FROM ranked_visits WHERE rn <= 3
),
seoul_gg_ok AS (
  SELECT user_id
  FROM last3
  GROUP BY user_id
  HAVING SUM(CASE WHEN sido_name LIKE '%서울%' OR sido_name LIKE '%경기%' OR sido_name LIKE '%인천%' THEN 1 ELSE 0 END) >= 1
),

-- ========== 나이 필터 (insured_person.birthday 사용) ==========
person AS (
  SELECT CAST(ip.user_id AS STRING) AS user_id, ip.birthday FROM insured_person ip WHERE ip.birthday IS NOT NULL
),
base_users AS (
  SELECT
    p.user_id,
    CASE
      WHEN p.birthday RLIKE '^[0-9]{8}$'
       AND SUBSTRING(p.birthday,5,2) BETWEEN '01' AND '12'
       AND SUBSTRING(p.birthday,7,2) BETWEEN '01' AND '31'
       AND NOT (SUBSTRING(p.birthday,5,2) IN ('04','06','09','11') AND SUBSTRING(p.birthday,7,2) = '31')
       AND NOT (SUBSTRING(p.birthday,5,2) = '02' AND CAST(SUBSTRING(p.birthday,7,2) AS INTEGER) > 29)
       AND NOT (SUBSTRING(p.birthday,5,2) = '02' AND SUBSTRING(p.birthday,7,2) = '29' AND NOT ((CAST(SUBSTRING(p.birthday,1,4) AS INTEGER) % 400 = 0) OR (CAST(SUBSTRING(p.birthday,1,4) AS INTEGER) % 4 = 0 AND CAST(SUBSTRING(p.birthday,1,4) AS INTEGER) % 100 <> 0)))
      THEN FLOOR(DATEDIFF(CURRENT_DATE, TO_DATE(p.birthday,'yyyyMMdd')) / 365.25)
      ELSE NULL
    END AS age_years
  FROM person p
),
base_users_filtered AS (
  SELECT user_id, age_years
  FROM base_users
  WHERE age_years BETWEEN {{ min_age }} AND {{ max_age }} -- 파라미터 2, 3
),

-- ========== 연락처 ==========
usr AS (
  SELECT CAST(u.id AS STRING) AS user_id, u.phone_number FROM `user` u
),

-- ========== 배제 조건 (최근 N개월로 제한) ==========
ex3_dementia_mci AS (
  SELECT DISTINCT b.user_id
  FROM bt b, params p WHERE b.treat_date >= p.dt_ex_window AND (b.disease_name LIKE '%알츠하이머%' OR b.disease_name LIKE '%치매%' OR b.disease_name LIKE '%인지장애%')
),
ex6_neuro AS (
  SELECT DISTINCT b.user_id
  FROM bt b, params p WHERE b.treat_date >= p.dt_ex_window AND (b.disease_name LIKE '%신경%' OR b.disease_name LIKE '%신경계%' OR b.disease_name LIKE '%뇌혈관%' OR b.disease_name LIKE '%뇌염%')
),
ex7_thyroid AS (
  SELECT DISTINCT b.user_id
  FROM bt b, params p WHERE b.treat_date >= p.dt_ex_window AND b.disease_name LIKE '%갑상선%'
),
ex8_infect_brain AS (
  SELECT DISTINCT b.user_id
  FROM bt b, params p WHERE b.treat_date >= p.dt_ex_window AND (b.disease_name LIKE '%뇌수막염%' OR b.disease_name LIKE '%뇌염%' OR b.disease_name LIKE '%뇌농양%')
),
ex9_tbi AS (
  SELECT DISTINCT b.user_id
  FROM bt b, params p WHERE b.treat_date >= p.dt_ex_window AND (b.disease_name LIKE '%외상성 뇌손상%' OR b.disease_name LIKE '%TBI%' OR b.disease_name LIKE '%두부 외상%')
),
ex11_immune AS (
  SELECT DISTINCT b.user_id
  FROM bt b, params p WHERE b.treat_date >= p.dt_ex_window AND b.disease_code LIKE 'M%'
),
ex12_systemic AS (
  SELECT DISTINCT b.user_id
  FROM bt b, params p WHERE b.treat_date >= p.dt_ex_window AND (b.disease_name LIKE '%간경변%' OR b.disease_name LIKE '%간부전%' OR b.disease_name LIKE '%신부전%' OR b.disease_name LIKE '%허혈성 심질환%' OR b.disease_name LIKE '%심부전%' OR b.disease_name LIKE '%관상동맥%' OR b.disease_name LIKE '%폐질환%' OR b.disease_name LIKE '%만성 폐%' OR b.disease_name LIKE '%내분비%' OR b.disease_name LIKE '%자가면역%' OR b.disease_name LIKE '%류마티스%' OR b.disease_name LIKE '%대사성%')
),
ex13_cancer AS (
  SELECT DISTINCT b.user_id
  FROM bt b, params p WHERE b.treat_date >= p.dt_ex_window AND (b.disease_name LIKE '%암%' OR b.disease_name LIKE '%종양%' OR b.disease_name LIKE '%신생물%')
),
ex14_prohibited_therapy AS (
  SELECT DISTINCT d.user_id
  FROM dt d, params p JOIN (SELECT 'CARDIOVERSION' AS kw UNION ALL SELECT 'PACEMAKER INSERTION' UNION ALL SELECT 'ABLATION' UNION ALL SELECT 'ICD IMPLANT') t ON (d.code_name LIKE CONCAT('%', t.kw, '%') OR d.treat_type LIKE CONCAT('%', t.kw, '%'))
  WHERE d.treat_date >= p.dt_ex_window
),
ex15_brady_drugs AS (
  SELECT DISTINCT p.user_id
  FROM pd p, params pa JOIN (SELECT 'ATENOLOL' AS kw UNION ALL SELECT 'METOPROLOL' UNION ALL SELECT 'BISOPROLOL' UNION ALL SELECT 'PROPRANOLOL' UNION ALL SELECT 'CARVEDILOL' UNION ALL SELECT 'NEBIVOLOL' UNION ALL SELECT 'VERAPAMIL' UNION ALL SELECT 'DILTIAZEM' UNION ALL SELECT 'DIGOXIN' UNION ALL SELECT 'AMIODARONE' UNION ALL SELECT 'SOTALOL' UNION ALL SELECT 'FLECAINIDE' UNION ALL SELECT 'PROPAFENONE' UNION ALL SELECT 'QUINIDINE' UNION ALL SELECT 'LIDOCAINE' UNION ALL SELECT 'LITHIUM' UNION ALL SELECT 'AMITRIPTYLINE' UNION ALL SELECT 'CLONIDINE') dl ON (p.ingredients LIKE CONCAT('%', dl.kw, '%') OR p.drug_name LIKE CONCAT('%', dl.kw, '%'))
  WHERE p.treat_date >= pa.dt_ex_window
),
ex16_arrhythmia_ihd AS (
  SELECT DISTINCT b.user_id
  FROM bt b, params p WHERE b.treat_date >= p.dt_ex_window AND (b.disease_name LIKE '%부정맥%' OR b.disease_name LIKE '%세동%' OR b.disease_name LIKE '%조동%' OR b.disease_name LIKE '%동정지%' OR b.disease_name LIKE '%허혈성 심질환%' OR b.disease_name LIKE '%심근허혈%' OR b.disease_name LIKE '%방실차단%' OR b.disease_name LIKE '%심장 수술%')
),
ex17_cog_risk AS (
  SELECT DISTINCT b.user_id
  FROM bt b, params p WHERE b.treat_date >= p.dt_ex_window AND (b.disease_name LIKE '%파킨슨%' OR b.disease_name LIKE '%정신%'  OR b.disease_name LIKE '%우울%' OR b.disease_name LIKE '%정신병%' OR b.disease_name LIKE '%조울%' OR b.disease_name LIKE '%양극성%')
),

-- ========== 최종 결과 ==========
final_candidates AS (
  SELECT u.user_id, u.age_years AS age
  FROM base_users_filtered u
  JOIN seoul_gg_ok loc ON u.user_id = loc.user_id
  LEFT JOIN ex3_dementia_mci      e3  ON u.user_id = e3.user_id
  LEFT JOIN ex6_neuro             e6  ON u.user_id = e6.user_id
  LEFT JOIN ex7_thyroid           e7  ON u.user_id = e7.user_id
  LEFT JOIN ex8_infect_brain      e8  ON u.user_id = e8.user_id
  LEFT JOIN ex9_tbi               e9  ON u.user_id = e9.user_id
  LEFT JOIN ex11_immune           e11 ON u.user_id = e11.user_id
  LEFT JOIN ex12_systemic         e12 ON u.user_id = e12.user_id
  LEFT JOIN ex13_cancer           e13 ON u.user_id = e13.user_id
  LEFT JOIN ex14_prohibited_therapy e14 ON u.user_id = e14.user_id
  LEFT JOIN ex15_brady_drugs      e15 ON u.user_id = e15.user_id
  LEFT JOIN ex16_arrhythmia_ihd   e16 ON u.user_id = e16.user_id
  LEFT JOIN ex17_cog_risk         e17 ON u.user_id = e17.user_id
  WHERE
      e3.user_id  IS NULL AND e6.user_id  IS NULL AND e7.user_id  IS NULL AND e8.user_id  IS NULL AND
      e9.user_id  IS NULL AND e11.user_id IS NULL AND e12.user_id IS NULL AND e13.user_id IS NULL AND
      e14.user_id IS NULL AND e15.user_id IS NULL AND e16.user_id IS NULL AND e17.user_id IS NULL
)

SELECT
  f.user_id,
  f.age,
  u.phone_number
FROM final_candidates f
LEFT JOIN usr u ON f.user_id = u.user_id
ORDER BY f.user_id;