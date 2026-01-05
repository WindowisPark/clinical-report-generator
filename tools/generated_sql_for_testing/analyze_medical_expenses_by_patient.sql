-- Generated from: analyze_medical_expenses_by_patient.yaml
-- Parameters used: {'user_id': 10, 'start_date': '2022-01-01', 'end_date': '2024-12-31', 'snapshot_dt': '2025-09-01'}

-- 특정 환자의 기간별 의료비 지출 현황 분석
-- 파라미터: user_id = 10, start_date = 2022-01-01, end_date = 2024-12-31

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
)
SELECT
    user_id,
    res_company_name,
    DATE_FORMAT(payment_date, 'yyyy-MM') AS payment_month,
    COUNT(*) AS expense_count,
    SUM(amount_krw) AS total_amount_krw,
    AVG(amount_krw) AS avg_amount_krw,
    MIN(amount_krw) AS min_amount_krw,
    MAX(amount_krw) AS max_amount_krw,
    MIN(payment_date) AS first_payment_date,
    MAX(payment_date) AS last_payment_date
FROM vw_nts_details_flat
WHERE user_id = 10
  AND payment_date >= '2022-01-01'
  AND payment_date <= '2024-12-31'
  AND amount_krw IS NOT NULL
  AND amount_krw > 0
GROUP BY user_id, res_company_name, DATE_FORMAT(payment_date, 'yyyy-MM')
ORDER BY payment_month DESC, total_amount_krw DESC
LIMIT 10000;