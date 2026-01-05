-- ✅ 1) 기본 정보: 나이/성별 계산 + 방문기록
-- 파라미터: user_id = {{ user_id }}

WITH ui AS (
  SELECT
      ip.user_id,
      ip.gender,
      FLOOR(DATEDIFF(CURRENT_DATE, TO_DATE(ip.birthday, 'yyyyMMdd')) / 365.25) AS age
  FROM insured_person ip
  WHERE ip.user_id = {{ user_id }}
),

bt AS (
  SELECT
      bt.user_id,
      TO_DATE(bt.res_treat_start_date, 'yyyyMMdd') AS visit_date,
      bt.res_hospital_name,
      bt.res_disease_name,
      bt.res_disease_code
  FROM basic_treatment bt
  WHERE bt.user_id = {{ user_id }}
    AND bt.deleted = FALSE
),
-- ✅ 2) 처방 원본: 날짜 파싱 + 빈 약명/성분 제거
rx_raw AS (
  SELECT
      pd.user_id,
      TO_DATE(pd.res_treat_start_date, 'yyyyMMdd') AS rx_date,
      TRIM(pd.res_drug_name)        AS res_drug_name,
      TRIM(pd.res_ingredients)      AS res_ingredients
  FROM prescribed_drug pd
  WHERE pd.user_id = {{ user_id }}
    AND pd.deleted = FALSE
    AND ((pd.res_drug_name IS NOT NULL AND TRIM(pd.res_drug_name) <> '')
         OR (pd.res_ingredients IS NOT NULL AND TRIM(pd.res_ingredients) <> ''))
),

-- ✅ 3) 처방을 날짜별로 집계(한 셀에 합치기)
rx_agg AS (
  SELECT
      user_id,
      rx_date,
      CONCAT_WS(', ', SORT_ARRAY(COLLECT_SET(res_drug_name)))      AS drug_names,
      CONCAT_WS(', ', SORT_ARRAY(COLLECT_SET(res_ingredients)))    AS drug_ingredients
  FROM rx_raw
  GROUP BY user_id, rx_date
),
-- ✅ 4) 방문일과 처방일 "정확히 같은 날" 매칭
exact_match AS (
  SELECT
      b.user_id,
      b.visit_date,
      r.drug_names,
      r.drug_ingredients
  FROM bt b
  LEFT JOIN rx_agg r
    ON b.user_id = r.user_id
   AND b.visit_date = r.rx_date
),
-- ✅ 5) 정확 매칭이 없으면 ±3일 내에서 "가장 가까운 처방일"을 선택
closest_match AS (
  SELECT *
  FROM (
    SELECT
        b.user_id,
        b.visit_date,
        r.drug_names,
        r.drug_ingredients,
        ROW_NUMBER() OVER (
          PARTITION BY b.user_id, b.visit_date
          ORDER BY ABS(DATEDIFF(r.rx_date, b.visit_date)) ASC,
                   r.rx_date DESC
        ) AS rn
    FROM bt b
    LEFT JOIN rx_agg r
      ON b.user_id = r.user_id
     AND r.rx_date BETWEEN DATE_SUB(b.visit_date, 3) AND DATE_ADD(b.visit_date, 3)
  ) x
  WHERE rn = 1
),
-- ✅ 6) 최종: 정확 매칭 우선, 없으면 근접 매칭 채움
visit_with_rx AS (
  SELECT
      b.user_id,
      b.visit_date,
      b.res_hospital_name,
      b.res_disease_name,
      b.res_disease_code,
      COALESCE(e.drug_names, c.drug_names)           AS drug_names,
      COALESCE(e.drug_ingredients, c.drug_ingredients) AS drug_ingredients
  FROM bt b
  LEFT JOIN exact_match   e ON b.user_id = e.user_id AND b.visit_date = e.visit_date
  LEFT JOIN closest_match c ON b.user_id = c.user_id AND b.visit_date = c.visit_date
)
-- ✅ 7) 출력: 유저 기본정보 + 방문이력 + 약/성분
SELECT
    ui.user_id,
    ui.age,
    ui.gender,
    DATE_FORMAT(v.visit_date, 'yyyyMMdd') AS res_treat_start_date,
    v.res_hospital_name,
    v.res_disease_name,
    v.res_disease_code,
    v.drug_names,
    v.drug_ingredients
FROM ui
JOIN visit_with_rx v
  ON ui.user_id = v.user_id
ORDER BY v.visit_date, v.res_hospital_name;