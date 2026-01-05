-- 질병 진행 패턴 분석 (A질환에서 B질환으로의 진행)
-- 파라미터: from_disease_keyword = {{ from_disease_keyword }}, to_disease_keyword = {{ to_disease_keyword }}

WITH from_disease AS (
  SELECT
    CAST(user_id AS STRING) AS user_id,
    MIN(to_date(res_treat_start_date, 'yyyyMMdd')) AS from_disease_first_date
  FROM basic_treatment
  WHERE res_disease_name LIKE '%{{ from_disease_keyword }}%'
    AND res_treat_start_date RLIKE '^[0-9]{8}$'
    AND deleted = FALSE
  GROUP BY user_id
),
to_disease AS (
  SELECT
    CAST(user_id AS STRING) AS user_id,
    MIN(to_date(res_treat_start_date, 'yyyyMMdd')) AS to_disease_first_date
  FROM basic_treatment
  WHERE res_disease_name LIKE '%{{ to_disease_keyword }}%'
    AND res_treat_start_date RLIKE '^[0-9]{8}$'
    AND deleted = FALSE
  GROUP BY user_id
),
joined AS (
  SELECT
    t.user_id,
    f.from_disease_first_date,
    t.to_disease_first_date,
    DATEDIFF(t.to_disease_first_date, f.from_disease_first_date) AS days_to_progression
  FROM to_disease t
  INNER JOIN from_disease f
    ON t.user_id = f.user_id
  WHERE t.to_disease_first_date >= f.from_disease_first_date
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
