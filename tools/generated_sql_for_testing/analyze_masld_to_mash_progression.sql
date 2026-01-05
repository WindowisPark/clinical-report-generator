-- Generated from: analyze_masld_to_mash_progression.yaml
-- Parameters used: {'from_disease_keyword': '지방간', 'to_disease_keyword': '염증성 간질환', 'snapshot_dt': '2025-09-01'}

-- MASLD(지방간)에서 MASH(염증성 간질환)로의 질병 진행 패턴 분석

WITH masld AS (
  SELECT
    CAST(user_id AS STRING) AS user_id,
    MIN(to_date(res_treat_start_date, 'yyyyMMdd')) AS masld_first_date
  FROM basic_treatment
  WHERE res_disease_name LIKE '%지방간%'
    AND res_treat_start_date RLIKE '^[0-9]{8}
joined AS (
  SELECT
    m.user_id,
    masld.masld_first_date,
    m.mash_first_date,
    DATEDIFF(m.mash_first_date, masld.masld_first_date) AS days_to_progression
  FROM mash m
  INNER JOIN masld masld
    ON m.user_id = masld.user_id
  WHERE m.mash_first_date >= masld.masld_first_date
),
binned_progression AS (
  SELECT
    days_to_progression,
    CASE
      WHEN days_to_progression <= 30 THEN '0-30 days'
      WHEN days_to_progression <= 90 THEN '31-90 days'
      WHEN days_to_progression <= 180 THEN '91-180 days'
      WHEN days_to_progression <= 365 THEN '181-365 days'
      ELSE '> 365 days'
    END AS progression_bin
  FROM joined
)
SELECT
  progression_bin,
  COUNT(*) AS patient_count
FROM binned_progression
GROUP BY progression_bin
ORDER BY MIN(days_to_progression);
    AND deleted = FALSE
  GROUP BY user_id
),
mash AS (
  SELECT
    CAST(user_id AS STRING) AS user_id,
    MIN(to_date(res_treat_start_date, 'yyyyMMdd')) AS mash_first_date
  FROM basic_treatment
  WHERE res_disease_name LIKE '%염증성 간질환%'
    AND res_treat_start_date RLIKE '^[0-9]{8}
joined AS (
  SELECT
    m.user_id,
    masld.masld_first_date,
    m.mash_first_date,
    DATEDIFF(m.mash_first_date, masld.masld_first_date) AS days_to_progression
  FROM mash m
  INNER JOIN masld masld
    ON m.user_id = masld.user_id
  WHERE m.mash_first_date >= masld.masld_first_date
),
binned_progression AS (
  SELECT
    days_to_progression,
    CASE
      WHEN days_to_progression <= 30 THEN '0-30 days'
      WHEN days_to_progression <= 90 THEN '31-90 days'
      WHEN days_to_progression <= 180 THEN '91-180 days'
      WHEN days_to_progression <= 365 THEN '181-365 days'
      ELSE '> 365 days'
    END AS progression_bin
  FROM joined
)
SELECT
  progression_bin,
  COUNT(*) AS patient_count
FROM binned_progression
GROUP BY progression_bin
ORDER BY MIN(days_to_progression);
    AND deleted = FALSE
  GROUP BY user_id
),
joined AS (
  SELECT
    m.user_id,
    masld.masld_first_date,
    m.mash_first_date,
    DATEDIFF(m.mash_first_date, masld.masld_first_date) AS days_to_progression
  FROM mash m
  INNER JOIN masld masld
    ON m.user_id = masld.user_id
  WHERE m.mash_first_date >= masld.masld_first_date
),
binned_progression AS (
  SELECT
    days_to_progression,
    CASE
      WHEN days_to_progression <= 30 THEN '0-30 days'
      WHEN days_to_progression <= 90 THEN '31-90 days'
      WHEN days_to_progression <= 180 THEN '91-180 days'
      WHEN days_to_progression <= 365 THEN '181-365 days'
      ELSE '> 365 days'
    END AS progression_bin
  FROM joined
)
SELECT
  progression_bin,
  COUNT(*) AS patient_count
FROM binned_progression
GROUP BY progression_bin
ORDER BY MIN(days_to_progression);