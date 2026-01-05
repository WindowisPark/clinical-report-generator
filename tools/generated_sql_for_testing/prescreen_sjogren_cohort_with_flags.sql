-- Generated from: prescreen_sjogren_cohort_with_flags.yaml
-- Parameters used: {'snapshot_dt': '2025-09-01'}

-- 쉐그렌 증후군 환자 사전 스크리닝 - 상세 포함/제외 기준별 플래그 생성

WITH params AS (
  SELECT
    CURRENT_DATE AS today,
    ADD_MONTHS(CURRENT_DATE, -3)  AS dt_12w_ago,  -- 12주 ≈ 3개월
    ADD_MONTHS(CURRENT_DATE, -12) AS dt_1y_ago,   -- 1년
    ADD_MONTHS(CURRENT_DATE, -6)  AS dt_6m_ago,   -- 6개월
    ADD_MONTHS(CURRENT_DATE, -1)  AS dt_4w_ago    -- 4주(≈1개월)
),
/* ---------- 공통: yyyyMMdd 키 생성 -> 안전 TO_DATE ---------- */
bt_norm AS (
  SELECT
    CAST(bt.user_id AS STRING)                 AS user_id,
    UPPER(COALESCE(bt.res_disease_name, ''))   AS disease_name,
    UPPER(COALESCE(bt.res_disease_code, ''))   AS disease_code,
    CONCAT(
      REGEXP_EXTRACT(CAST(bt.res_treat_start_date AS STRING), '(\\d{4})', 1),
      REGEXP_EXTRACT(CAST(bt.res_treat_start_date AS STRING), '(\\d{4})[-/]?(\\d{2})', 2),
      REGEXP_EXTRACT(CAST(bt.res_treat_start_date AS STRING), '(\\d{4})[-/]?(\\d{2})[-/]?(\\d{2})', 3)
    ) AS treat_key_raw
  FROM basic_treatment bt
  WHERE bt.deleted = FALSE
),
bt AS (
  SELECT
    user_id, disease_name, disease_code,
    CASE WHEN treat_key_raw RLIKE '^[0-9]{8}$' THEN TO_DATE(treat_key_raw, 'yyyyMMdd') END AS treat_date
  FROM bt_norm
  WHERE treat_key_raw RLIKE '^[0-9]{8}$'
),

pd_norm AS (
  SELECT
    CAST(pd.user_id AS STRING)                  AS user_id,
    UPPER(COALESCE(pd.res_drug_name, ''))       AS drug_name,
    UPPER(COALESCE(pd.res_ingredients, ''))     AS ingredients,
    COALESCE(pd.res_one_dose, '')               AS one_dose_txt,
    COALESCE(pd.res_total_dosing_days, '')      AS total_days_txt,
    CONCAT(
      REGEXP_EXTRACT(CAST(pd.res_treat_start_date AS STRING), '(\\d{4})', 1),
      REGEXP_EXTRACT(CAST(pd.res_treat_start_date AS STRING), '(\\d{4})[-/]?(\\d{2})', 2),
      REGEXP_EXTRACT(CAST(pd.res_treat_start_date AS STRING), '(\\d{4})[-/]?(\\d{2})[-/]?(\\d{2})', 3)
    ) AS treat_key_raw
  FROM prescribed_drug pd
  WHERE pd.deleted = FALSE
),
pd AS (
  SELECT
    user_id, drug_name, ingredients,
    -- 용량(mg) 추정: 약명/성분의 "..MG" 수치 → 없으면 one_dose_txt 숫자
    TRY_CAST(
      COALESCE(
        REGEXP_EXTRACT(drug_name, '([0-9]+\\.?[0-9]*)\\s*MG', 1),
        REGEXP_EXTRACT(ingredients, '([0-9]+\\.?[0-9]*)\\s*MG', 1),
        NULLIF(REGEXP_REPLACE(one_dose_txt, '[^0-9\\.]', ''), '')
      ) AS DOUBLE
    ) AS dose_mg,
    CAST(NULLIF(total_days_txt, '') AS INT) AS total_dosing_days,
    CASE WHEN treat_key_raw RLIKE '^[0-9]{8}$' THEN TO_DATE(treat_key_raw, 'yyyyMMdd') END AS treat_date
  FROM pd_norm
  WHERE treat_key_raw RLIKE '^[0-9]{8}$'
),

dt_norm AS (
  SELECT
    CAST(dt.user_id AS STRING)                  AS user_id,
    UPPER(COALESCE(dt.res_code_name, ''))       AS code_name,
    UPPER(COALESCE(dt.res_treat_type, ''))      AS treat_type,
    CONCAT(
      REGEXP_EXTRACT(CAST(dt.res_treat_start_date AS STRING), '(\\d{4})', 1),
      REGEXP_EXTRACT(CAST(dt.res_treat_start_date AS STRING), '(\\d{4})[-/]?(\\d{2})', 2),
      REGEXP_EXTRACT(CAST(dt.res_treat_start_date AS STRING), '(\\d{4})[-/]?(\\d{2})[-/]?(\\d{2})', 3)
    ) AS treat_key_raw
  FROM detail_treatment dt
  WHERE dt.deleted = FALSE
),
dt AS (
  SELECT
    user_id, code_name, treat_type,
    CASE WHEN treat_key_raw RLIKE '^[0-9]{8}$' THEN TO_DATE(treat_key_raw, 'yyyyMMdd') END AS treat_date
  FROM dt_norm
  WHERE treat_key_raw RLIKE '^[0-9]{8}$'
),

/* ---------- 안전 DOB 파싱(윤년·없는 날짜 차단) & 나이 계산 ---------- */
ip_safe AS (
  SELECT
    CAST(ip.user_id AS STRING) AS user_id,
    CASE
      WHEN ip.birthday RLIKE '^(19|20)[0-9]{6}$'
       AND SUBSTRING(ip.birthday,5,2) BETWEEN '01' AND '12'
       AND SUBSTRING(ip.birthday,7,2) BETWEEN '01' AND '31'
       AND NOT (SUBSTRING(ip.birthday,5,2) IN ('04','06','09','11') AND SUBSTRING(ip.birthday,7,2) = '31')
       AND NOT (SUBSTRING(ip.birthday,5,2) = '02' AND CAST(SUBSTRING(ip.birthday,7,2) AS INT) > 29)
       AND NOT (
         SUBSTRING(ip.birthday,5,2) = '02' AND SUBSTRING(ip.birthday,7,2) = '29'
         AND NOT (
           (CAST(SUBSTRING(ip.birthday,1,4) AS INT) % 400 = 0)
           OR (CAST(SUBSTRING(ip.birthday,1,4) AS INT) % 4 = 0 AND CAST(SUBSTRING(ip.birthday,1,4) AS INT) % 100 <> 0)
         )
       )
      THEN TO_DATE(ip.birthday, 'yyyyMMdd')
    END AS dob
  FROM insured_person ip
),

/* ---------- 1) Base: Sjögren's ---------- */
base_sjogren AS (
  SELECT DISTINCT b.user_id
  FROM bt b
  WHERE b.disease_name LIKE '%SJOGREN%' OR b.disease_name LIKE '%쉐그렌%'
     OR b.disease_code LIKE 'M35.0%'
),

/* ---------- 2) Inclusion ---------- */
incl_age18 AS (
  SELECT i.user_id
  FROM ip_safe i
  WHERE i.dob IS NOT NULL
    AND FLOOR(MONTHS_BETWEEN(CURRENT_DATE, i.dob)/12) >= 18
),
-- Prednisone 저용량(부분): 성분/약명 매칭 + 추정 dose_mg < 10 + 누적 복약일수 ≥ 42일
incl_prednisone AS (
  SELECT DISTINCT p.user_id
  FROM pd p
  WHERE (p.ingredients LIKE '%PREDNISONE%' OR p.drug_name LIKE '%PREDNISONE%' OR p.drug_name LIKE '%프레드니손%')
    AND p.dose_mg IS NOT NULL AND p.dose_mg < 10
    AND p.total_dosing_days IS NOT NULL AND p.total_dosing_days >= 42
),
/* ---------- 3) Exclusions (feasible/partial) ---------- */
ex_autoimmune AS (
  SELECT DISTINCT user_id
  FROM bt
  WHERE disease_name LIKE '%RHEUMATOID ARTHRITIS%' OR disease_name LIKE '% RA %' OR disease_name LIKE '%류마티스%'
     OR disease_name LIKE '%SYSTEMIC LUPUS%' OR disease_name LIKE '% SLE %' OR disease_name LIKE '%루푸스%'
     OR disease_name LIKE '%SCLERODERMA%' OR disease_name LIKE '%SYSTEMIC SCLEROSIS%' OR disease_name LIKE '%경피%'
),
ex_non_sjd_sicca AS (
  SELECT DISTINCT user_id
  FROM bt
  WHERE disease_name LIKE '%RADIATION%' OR disease_name LIKE '%방사선%'
     OR disease_name LIKE '%SARCOIDOSIS%' OR disease_name LIKE '%사르코이드%'
     OR disease_name LIKE '%GRAFT-VERSUS-HOST%' OR disease_name LIKE '%GVHD%'
),
ex_fibromyalgia AS (
  SELECT DISTINCT user_id
  FROM bt
  WHERE disease_name LIKE '%FIBROMYALGIA%' OR disease_name LIKE '%섬유근%'
),
ex_asplenia AS (
  SELECT DISTINCT user_id
  FROM bt
  WHERE disease_name LIKE '%ASPLENIA%' OR disease_name LIKE '%무비증%' OR disease_name LIKE '%SPLENECTOMY%' OR disease_name LIKE '%절제%'
),
ex_recent_oph AS (
  SELECT DISTINCT d.user_id
  FROM dt d
  JOIN params p ON 1=1
  WHERE (
          (d.code_name LIKE '%CATARACT%' OR d.code_name LIKE '%백내장%')
          AND d.treat_date >= p.dt_6m_ago
        )
     OR (
          (d.code_name LIKE '%PUNCTAL PLUG%' OR d.code_name LIKE '%눈물점%' OR d.code_name LIKE '%누점%')
          AND d.treat_date >= p.dt_4w_ago
        )
),
ex_corneal_tx AS (
  SELECT DISTINCT d.user_id
  FROM dt d
  JOIN params p ON 1=1
  WHERE (d.code_name LIKE '%PENETRATING KERATOPLASTY%' OR d.code_name LIKE '%KERATOPLASTY%' OR d.code_name LIKE '%이식%')
    AND d.treat_date >= p.dt_1y_ago
),
ex_ild AS (
  SELECT DISTINCT user_id
  FROM bt
  WHERE disease_name LIKE '%INTERSTITIAL LUNG DISEASE%' OR disease_name LIKE '% ILD %' OR disease_name LIKE '%간질%'
     OR disease_name LIKE '%NSIP%' OR disease_name LIKE '%UIP%' OR disease_name LIKE '%LIP%' OR disease_name LIKE '%ORGANIZING PNEUMONIA%'
),
ex_recent_cvd AS (
  SELECT DISTINCT b.user_id
  FROM bt b
  JOIN params p ON 1=1
  WHERE b.treat_date >= p.dt_12w_ago
    AND (
      b.disease_name LIKE '%MYOCARDIAL INFARCTION%' OR b.disease_name LIKE '%심근%'
      OR b.disease_name LIKE '%ISCHEMIC HEART%'       OR b.disease_name LIKE '%허혈성%'
      OR b.disease_name LIKE '%STROKE%'               OR b.disease_name LIKE '%뇌졸%'
    )
),
ex_aps AS (
  SELECT DISTINCT b.user_id
  FROM bt b
  JOIN params p ON 1=1
  WHERE (b.disease_name LIKE '%ANTIPHOSPHOLIPID%' OR b.disease_name LIKE '% APS %' OR b.disease_name LIKE '%항인지%')
    AND b.treat_date >= p.dt_1y_ago
),
ex_viral AS (
  SELECT DISTINCT user_id
  FROM bt
  WHERE disease_name LIKE '%HEPATITIS B%' OR disease_name LIKE '% HBV %' OR disease_name LIKE '%B형%'
     OR disease_name LIKE '%HEPATITIS C%' OR disease_name LIKE '% HCV %' OR disease_name LIKE '%C형%'
     OR disease_name LIKE '%HIV%' OR disease_name LIKE '%HUMAN IMMUNODEFICIENCY%'
),
ex_sss_risk AS (
  SELECT DISTINCT user_id
  FROM bt
  WHERE disease_name LIKE '%MYOCARDITIS%' OR disease_name LIKE '%PERICARDITIS%' OR disease_name LIKE '%염증성 심질환%'
     OR disease_name LIKE '%RHEUMATIC HEART%' OR disease_name LIKE '%류마티스심장%'
     OR disease_name LIKE '%ARTERITIS%' OR disease_name LIKE '%동맥염%'
     OR disease_name LIKE '%LUPUS%'
),

/* ---------- Cohort 조립 ---------- */
eligible_users AS (
  SELECT DISTINCT b.user_id
  FROM base_sjogren b
  INNER JOIN incl_age18 a ON b.user_id = a.user_id    -- Age ≥ 18 필수
)

SELECT
  u.user_id,
  -- 참고 플래그(부분 충족·모니터링)
  CASE WHEN p.user_id   IS NOT NULL THEN TRUE ELSE FALSE END AS on_lowdose_prednisone_flag,

  -- Exclusion flags
  CASE WHEN ea.user_id  IS NOT NULL THEN TRUE ELSE FALSE END AS ex_autoimmune_flag,
  CASE WHEN ns.user_id  IS NOT NULL THEN TRUE ELSE FALSE END AS ex_non_sjd_sicca_flag,
  CASE WHEN fm.user_id  IS NOT NULL THEN TRUE ELSE FALSE END AS ex_fibromyalgia_flag,
  CASE WHEN aspl.user_id IS NOT NULL THEN TRUE ELSE FALSE END AS ex_asplenia_flag,
  CASE WHEN oph.user_id IS NOT NULL THEN TRUE ELSE FALSE END AS ex_recent_oph_flag,
  CASE WHEN ctx.user_id IS NOT NULL THEN TRUE ELSE FALSE END AS ex_corneal_tx_flag,
  CASE WHEN ild.user_id IS NOT NULL THEN TRUE ELSE FALSE END AS ex_ild_flag,
  CASE WHEN cvd.user_id IS NOT NULL THEN TRUE ELSE FALSE END AS ex_recent_cvd_flag,
  CASE WHEN aps.user_id IS NOT NULL THEN TRUE ELSE FALSE END AS ex_aps_flag,
  CASE WHEN vir.user_id IS NOT NULL THEN TRUE ELSE FALSE END AS ex_viral_pos_flag,
  CASE WHEN sss.user_id IS NOT NULL THEN TRUE ELSE FALSE END AS ex_sss_risk_flag,
  -- 최종 제외 여부
  (
    (ea.user_id  IS NOT NULL) OR
    (ns.user_id  IS NOT NULL) OR
    (fm.user_id  IS NOT NULL) OR
    (aspl.user_id IS NOT NULL) OR
    (oph.user_id IS NOT NULL) OR
    (ctx.user_id IS NOT NULL) OR
    (ild.user_id IS NOT NULL) OR
    (cvd.user_id IS NOT NULL) OR
    (aps.user_id IS NOT NULL) OR
    (vir.user_id IS NOT NULL) OR
    (sss.user_id IS NOT NULL)
  ) AS any_exclusion_flag

FROM eligible_users u
LEFT JOIN incl_prednisone   p    ON u.user_id = p.user_id
LEFT JOIN ex_autoimmune     ea   ON u.user_id = ea.user_id
LEFT JOIN ex_non_sjd_sicca  ns   ON u.user_id = ns.user_id
LEFT JOIN ex_fibromyalgia   fm   ON u.user_id = fm.user_id
LEFT JOIN ex_asplenia       aspl ON u.user_id = aspl.user_id
LEFT JOIN ex_recent_oph     oph  ON u.user_id = oph.user_id
LEFT JOIN ex_corneal_tx     ctx  ON u.user_id = ctx.user_id
LEFT JOIN ex_ild            ild  ON u.user_id = ild.user_id
LEFT JOIN ex_recent_cvd     cvd  ON u.user_id = cvd.user_id
LEFT JOIN ex_aps            aps  ON u.user_id = aps.user_id
LEFT JOIN ex_viral          vir  ON u.user_id = vir.user_id
LEFT JOIN ex_sss_risk       sss  ON u.user_id = sss.user_id
ORDER BY u.user_id;