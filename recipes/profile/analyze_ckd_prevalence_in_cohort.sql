-- 특정 질환 코호트 내에서 만성 신장병(CKD) 유병률 분석 (최적화 버전)
-- GROUP BY와 조건부 집계를 사용하여 basic_treatment 테이블 스캔을 1회로 줄임
-- 파라미터: cohort_disease_name = {{ cohort_disease_name }}, cohort_disease_code = {{ cohort_disease_code }}

WITH user_flags AS (
  SELECT
    user_id,
    -- 1) 코호트 정의: 병명에 특정 질환명 또는 질환 코드 문구 포함
    MAX(CASE
      WHEN UPPER(COALESCE(res_disease_name,'')) LIKE UPPER('%{{ cohort_disease_name }}%')
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%{{ cohort_disease_code }}%'
      THEN 1 ELSE 0 END
    ) as is_in_cohort,

    -- 2) CKD 1~5기 이력
    MAX(CASE
      WHEN UPPER(COALESCE(res_disease_code,'')) IN ('N18.1','N18.2','N18.3','N18.4','N18.5')
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%만성 신장병(1기)%'
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%만성 신장병(2기)%'
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%만성 신장병(3기)%'
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%만성 신장병(4기)%'
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%만성 신장병(5기)%'
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%CKD 1%'
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%CKD 2%'
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%CKD 3%'
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%CKD 4%'
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%CKD 5%'
      THEN 1 ELSE 0 END
    ) as has_ckd_1_5,

    -- 3) CKD 3기 이력
    MAX(CASE
      WHEN UPPER(COALESCE(res_disease_code,'')) = 'N18.3'
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%만성 신장병(3기)%'
        OR UPPER(COALESCE(res_disease_name,'')) LIKE '%CKD 3%'
      THEN 1 ELSE 0 END
    ) as has_ckd_3

  FROM basic_treatment
  WHERE deleted = FALSE
  GROUP BY user_id
)
SELECT
  SUM(is_in_cohort) AS cohort_users,
  SUM(CASE WHEN is_in_cohort = 1 AND has_ckd_1_5 = 1 THEN 1 ELSE 0 END) AS ckd_1_5_users,
  ROUND(100.0 * TRY_DIVIDE(SUM(CASE WHEN is_in_cohort = 1 AND has_ckd_1_5 = 1 THEN 1 ELSE 0 END), SUM(is_in_cohort)), 1) AS ckd_1_5_pct_of_cohort,
  SUM(CASE WHEN is_in_cohort = 1 AND has_ckd_3 = 1 THEN 1 ELSE 0 END) AS ckd3_users,
  ROUND(100.0 * TRY_DIVIDE(SUM(CASE WHEN is_in_cohort = 1 AND has_ckd_3 = 1 THEN 1 ELSE 0 END), SUM(is_in_cohort)), 1) AS ckd3_pct_of_cohort,
  ROUND(100.0 * TRY_DIVIDE(SUM(CASE WHEN is_in_cohort = 1 AND has_ckd_3 = 1 THEN 1 ELSE 0 END), SUM(CASE WHEN is_in_cohort = 1 AND has_ckd_1_5 = 1 THEN 1 ELSE 0 END)), 1) AS ckd3_pct_within_ckd_1_5
FROM user_flags;