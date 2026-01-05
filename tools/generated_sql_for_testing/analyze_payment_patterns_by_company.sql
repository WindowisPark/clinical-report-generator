-- Generated from: analyze_payment_patterns_by_company.yaml
-- Parameters used: {'analysis_period_start': '2022-01-01', 'analysis_period_end': '2024-12-31', 'snapshot_dt': '2025-09-01'}

-- 보험사별 결제 패턴 및 의료비 분석
-- 파라미터: analysis_period_start = 2022-01-01, analysis_period_end = 2024-12-31

WITH detail_norm AS (
  SELECT
      d.medical_expenses_detail_history_id,
      d.medical_expenses_history_id,
      -- 금액 정규화(문자 → 숫자, res_amount > res_total_amount > res_amount1)
      CAST(
        NULLIF(regexp_replace(COALESCE(d.res_amount, d.res_total_amount, d.res_amount1), '[^0-9]', ''), '')
        AS BIGINT
      ) AS amount_krw,
      -- 날짜: yyyyMMdd만 허용(유효 범위 검사 후 to_date)
      CASE
        WHEN d.res_date_payment RLIKE '^[0-9]{8}$'
             AND CAST(SUBSTRING(d.res_date_payment, 5, 2) AS INT) BETWEEN 1 AND 12
             AND CAST(SUBSTRING(d.res_date_payment, 7, 2) AS INT) BETWEEN 1 AND 31
          THEN to_date(d.res_date_payment, 'yyyyMMdd')
        ELSE NULL
      END AS payment_date,
      d.res_date_payment AS payment_date_raw
  FROM medical_expenses_detail_history d
),
vw_nts_details_flat AS (
  SELECT
    f.*,
    h.user_id,
    h.res_company_name,
    h.res_company_identity_no
  FROM detail_norm f
  JOIN medical_expenses_history h
    ON f.medical_expenses_history_id = h.medical_expenses_history_id
  WHERE h.deleted = FALSE
),
company_stats AS (
  SELECT
    res_company_name,
    res_company_identity_no,
    COUNT(DISTINCT user_id) AS unique_patients,
    COUNT(*) AS total_transactions,
    SUM(amount_krw) AS total_amount_krw,
    AVG(amount_krw) AS avg_amount_per_transaction,
    PERCENTILE(amount_krw, 0.5) AS median_amount_krw,
    MIN(payment_date) AS first_payment_date,
    MAX(payment_date) AS last_payment_date,
    COUNT(DISTINCT DATE_FORMAT(payment_date, 'yyyy-MM')) AS active_months
  FROM vw_nts_details_flat
  WHERE payment_date >= '2022-01-01'
    AND payment_date <= '2024-12-31'
    AND amount_krw IS NOT NULL
    AND amount_krw > 0
  GROUP BY res_company_name, res_company_identity_no
)
SELECT
    cs.res_company_name AS company_name,
    cs.total_amount_krw,
    cs.res_company_identity_no AS company_identity_no,
    cs.unique_patients,
    cs.total_transactions,
    FORMAT_NUMBER(cs.avg_amount_per_transaction, 0) AS avg_amount_per_transaction,
    FORMAT_NUMBER(cs.median_amount_krw, 0) AS median_amount_krw,
    cs.first_payment_date,
    cs.last_payment_date,
    cs.active_months,
    ROUND(cs.total_transactions / cs.active_months, 1) AS avg_monthly_transactions
FROM company_stats cs
WHERE cs.unique_patients >= 10  -- 최소 10명 이상의 환자가 있는 보험사만
ORDER BY cs.total_amount_krw DESC
LIMIT 50;