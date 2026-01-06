-- Generated from: analyze_drug_therapy_transition_sites.yaml
-- Parameters used: {'start_date': '2023-01-01', 'end_date': '2025-09-12', 'transition_window_days': 90, 'top_n': 50, 'snapshot_dt': '2025-09-01'}

WITH
-- 1) 처방 성분 정규화 파이프라인 (최적화) ----------------------------------
base AS (
  SELECT
    CAST(user_id AS STRING) AS user_id,
    CASE
      WHEN REGEXP_LIKE(CAST(res_treat_start_date AS STRING),'^[0-9]{8}
)
        THEN TO_DATE(CAST(res_treat_start_date AS STRING),'yyyyMMdd')
      WHEN REGEXP_LIKE(CAST(res_treat_start_date AS STRING),'^[0-9]{4}-[0-9]{2}-[0-9]{2}
)
        THEN TO_DATE(CAST(res_treat_start_date AS STRING),'yyyy-MM-dd')
      WHEN REGEXP_LIKE(CAST(res_treat_start_date AS STRING),'^[0-9]{4}/[0-9]{2}/[0-9]{2}
)
        THEN TO_DATE(CAST(res_treat_start_date AS STRING),'yyyy/MM/dd')
      ELSE NULL
    END AS rx_date,
    UPPER(REGEXP_REPLACE(REGEXP_REPLACE(CAST(res_ingredients AS STRING), '\\(AS [^)]+\\)', ''), '\\s+', '')) AS ingr_raw
  FROM prescribed_drug
  WHERE res_ingredients IS NOT NULL
    -- 최적화: 날짜 필터를 가장 첫 단계에 적용하여 처리 데이터 양을 최소화
    AND (
        CASE
            WHEN REGEXP_LIKE(CAST(res_treat_start_date AS STRING),'^[0-9]{8}
) THEN TO_DATE(CAST(res_treat_start_date AS STRING),'yyyyMMdd')
            WHEN REGEXP_LIKE(CAST(res_treat_start_date AS STRING),'^[0-9]{4}-[0-9]{2}-[0-9]{2}
) THEN TO_DATE(CAST(res_treat_start_date AS STRING),'yyyy-MM-dd')
            WHEN REGEXP_LIKE(CAST(res_treat_start_date AS STRING),'^[0-9]{4}/[0-9]{2}/[0-9]{2}
) THEN TO_DATE(CAST(res_treat_start_date AS STRING),'yyyy/MM/dd')
            ELSE NULL
        END
    ) BETWEEN DATE('2023-01-01') AND DATE('2025-09-12')
),
tokens AS (
  SELECT user_id, rx_date, TRIM(tok) AS tok
  FROM base
  LATERAL VIEW EXPLODE(SPLIT(ingr_raw, '[+/,]')) s AS tok
),
salt_clean AS (
  SELECT
    user_id, rx_date,
    REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(tok, '(CALCIUM|SODIUM|BESYLATE|MALEATE|MESYLATE|NICOTINATE|ADIPATE|OROTATE|ORATATE|CILEXETIL|CAMSYLATE|PENTAHYDRATE)', ''), '^S[-]?', ''), '-', ''), '\\.', ''), '\\s+', ''), '±', ''), '®', ''), '^\\s+|\\s+
, '') AS token_clean
  FROM tokens
  WHERE rx_date IS NOT NULL
),
norm AS (
  SELECT
    user_id, rx_date,
    CASE
      WHEN token_clean RLIKE 'CANDESARTAN'               THEN 'CANDESARTAN'
      WHEN token_clean RLIKE 'AMLODIPIN|암로디핀'            THEN 'AMLODIPINE'
      WHEN token_clean RLIKE 'ATORVASTATIN|아토르바스타틴'     THEN 'ATORVASTATIN'
      WHEN token_clean RLIKE 'ROSUVASTATIN|로수바스타틴'       THEN 'ROSUVASTATIN'
      WHEN token_clean RLIKE 'PITAVASTATIN|피타바스타틴'       THEN 'PITAVASTATIN'
      WHEN token_clean RLIKE 'SIMVASTATIN|심바스타틴'        THEN 'SIMVASTATIN'
      WHEN token_clean RLIKE 'PRAVASTATIN|프라바스타틴'      THEN 'PRAVASTATIN'
      WHEN token_clean RLIKE 'LOVASTATIN|로바스타틴'         THEN 'LOVASTATIN'
      WHEN token_clean RLIKE 'FLUVASTATIN|플루바스타틴'      THEN 'FLUVASTATIN'
      WHEN token_clean RLIKE 'FLUVOXAMINE'                 THEN NULL
      ELSE token_clean
    END AS ingredient
  FROM salt_clean
),
rx AS (
  SELECT
    user_id,
    rx_date,
    COLLECT_SET(ingredient) AS ingr_set
  FROM norm
  WHERE ingredient IS NOT NULL
  -- 최적화: 날짜 필터가 base CTE로 이동하여 여기서는 제거
  GROUP BY user_id, rx_date
),

-- 2) 코호트(단일제/병용)와 최초 인덱스 --------------------------------------
mono_idx AS (
  SELECT user_id, MIN(rx_date) AS first_index
  FROM rx
  WHERE ((ARRAY_CONTAINS(ingr_set,'CANDESARTAN') AND NOT ARRAY_CONTAINS(ingr_set,'AMLODIPINE')) OR (ARRAY_CONTAINS(ingr_set,'AMLODIPINE')  AND NOT ARRAY_CONTAINS(ingr_set,'CANDESARTAN')))
    AND SIZE(ARRAY_INTERSECT(ingr_set, ARRAY('ATORVASTATIN','ROSUVASTATIN','PITAVASTATIN','SIMVASTATIN','PRAVASTATIN','LOVASTATIN','FLUVASTATIN'))) = 0
  GROUP BY user_id
),
dual_idx AS (
  SELECT user_id, MIN(rx_date) AS first_index
  FROM rx
  WHERE ARRAY_CONTAINS(ingr_set,'CANDESARTAN')
    AND ARRAY_CONTAINS(ingr_set,'AMLODIPINE')
    AND SIZE(ARRAY_INTERSECT(ingr_set, ARRAY('ATORVASTATIN','ROSUVASTATIN','PITAVASTATIN','SIMVASTATIN','PRAVASTATIN','LOVASTATIN','FLUVASTATIN'))) = 0
  GROUP BY user_id
),

-- 3) 전환(<= N일) 탐지 ------------------------------------------------------
triple_from_mono AS (
  SELECT m.user_id, MIN(r.rx_date) AS triple_date, 'MONO->TRIPLE' AS path
  FROM mono_idx m
  JOIN rx r ON r.user_id = m.user_id AND r.rx_date BETWEEN m.first_index AND DATE_ADD(m.first_index, 90)
  WHERE (ARRAY_CONTAINS(r.ingr_set,'CANDESARTAN') AND ARRAY_CONTAINS(r.ingr_set,'AMLODIPINE'))
     OR SIZE(ARRAY_INTERSECT(r.ingr_set, ARRAY('ATORVASTATIN','ROSUVASTATIN','PITAVASTATIN','SIMVASTATIN','PRAVASTATIN','LOVASTATIN','FLUVASTATIN'))) > 0
  GROUP BY m.user_id
),
triple_from_dual AS (
  SELECT d.user_id, MIN(r.rx_date) AS triple_date, 'DUAL->TRIPLE' AS path
  FROM dual_idx d
  JOIN rx r ON r.user_id = d.user_id AND r.rx_date BETWEEN d.first_index AND DATE_ADD(d.first_index, 90)
  WHERE SIZE(ARRAY_INTERSECT(r.ingr_set, ARRAY('ATORVASTATIN','ROSUVASTATIN','PITAVASTATIN','SIMVASTATIN','PRAVASTATIN','LOVASTATIN','FLUVASTATIN'))) > 0
  GROUP BY d.user_id
),
coh_triple AS (
  SELECT * FROM triple_from_mono
  UNION ALL
  SELECT * FROM triple_from_dual
),

-- 4) 전환일 병원 매칭 --------------------------------------------------------
bt_parsed AS (
  SELECT
    CAST(user_id AS STRING) AS user_id,
    CASE
      WHEN REGEXP_LIKE(CAST(res_treat_start_date AS STRING),'^[0-9]{8}
) THEN TO_DATE(CAST(res_treat_start_date AS STRING),'yyyyMMdd')
      WHEN REGEXP_LIKE(CAST(res_treat_start_date AS STRING),'^[0-9]{4}-[0-9]{2}-[0-9]{2}
) THEN TO_DATE(CAST(res_treat_start_date AS STRING),'yyyy-MM-dd')
      WHEN REGEXP_LIKE(CAST(res_treat_start_date AS STRING),'^[0-9]{4}/[0-9]{2}/[0-9]{2}
) THEN TO_DATE(CAST(res_treat_start_date AS STRING),'yyyy/MM/dd')
      ELSE NULL
    END AS bt_dt,
    ANY_VALUE(res_hospital_code) AS hosp_code,
    ANY_VALUE(res_hospital_name) AS hosp_name
  FROM basic_treatment
  WHERE COALESCE(deleted, FALSE) = FALSE
  GROUP BY CAST(user_id AS STRING),
           CASE
             WHEN REGEXP_LIKE(CAST(res_treat_start_date AS STRING),'^[0-9]{8}
)
               THEN TO_DATE(CAST(res_treat_start_date AS STRING),'yyyyMMdd')
             WHEN REGEXP_LIKE(CAST(res_treat_start_date AS STRING),'^[0-9]{4}-[0-9]{2}-[0-9]{2}
)
               THEN TO_DATE(CAST(res_treat_start_date AS STRING),'yyyy-MM-dd')
             WHEN REGEXP_LIKE(CAST(res_treat_start_date AS STRING),'^[0-9]{4}/[0-9]{2}/[0-9]{2}
)
               THEN TO_DATE(CAST(res_treat_start_date AS STRING),'yyyy/MM/dd')
             ELSE NULL
           END
),
hospital_meta AS (
  SELECT
    h.hospital_code,
    CASE
      WHEN h.medical_facility_type_code IN ('01','1') THEN 3
      WHEN h.medical_facility_type_code IN ('11','21','28','29','41','92') THEN 2
      ELSE 1
    END AS facility_level,
    h.sido_name,
    h.sigungu_name
  FROM hospital h
),
triple_site AS (
  SELECT c.user_id, c.triple_date, b.hosp_code, b.hosp_name, hm.facility_level, hm.sido_name, hm.sigungu_name, c.path
  FROM coh_triple c
  LEFT JOIN bt_parsed b ON c.user_id = b.user_id AND c.triple_date = b.bt_dt
  LEFT JOIN hospital_meta hm ON b.hosp_code = hm.hospital_code
),

-- 5) 사이트 집계 + 러닝토탈 --------------------------------------------------
site_counts AS (
  SELECT
    COALESCE(hosp_name,'(미매칭)') AS site,
    facility_level,
    sido_name,
    sigungu_name,
    COUNT(DISTINCT user_id) AS triple_users
  FROM triple_site
  GROUP BY COALESCE(hosp_name,'(미매칭)'), facility_level, sido_name, sigungu_name
),
ranked AS (
  SELECT
    site, facility_level, sido_name, sigungu_name, triple_users,
    SUM(triple_users) OVER (ORDER BY triple_users DESC) AS running_total
  FROM site_counts
)

SELECT * FROM ranked
ORDER BY triple_users DESC
LIMIT 50;
