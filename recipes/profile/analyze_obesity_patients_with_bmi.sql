-- 비만 진단 + 건강검진 보유자 매칭 & 최신 BMI 부착
-- 파라미터: obesity_keyword = {{ obesity_keyword }}

WITH obese_users AS (
    -- 비만 진단(E66% 또는 진단명에 '비만') 보유자 + 첫 비만 진단일
    SELECT
        CAST(bt.user_id AS STRING) AS user_id,
        MIN(
            CASE
                WHEN bt.res_treat_start_date RLIKE '^[0-9]{8}$'
                AND CAST(SUBSTRING(bt.res_treat_start_date,1,4) AS INTEGER) BETWEEN 1900 AND YEAR(current_date())
                AND CAST(SUBSTRING(bt.res_treat_start_date,5,2) AS INTEGER) BETWEEN 1 AND 12
                AND CAST(SUBSTRING(bt.res_treat_start_date,7,2) AS INTEGER) BETWEEN 1 AND 31
                -- 윤년 2/29 검증
                AND NOT (
                    CAST(SUBSTRING(bt.res_treat_start_date,5,2) AS INTEGER) = 2
                    AND CAST(SUBSTRING(bt.res_treat_start_date,7,2) AS INTEGER) = 29
                    AND MOD(CAST(SUBSTRING(bt.res_treat_start_date,1,4) AS INTEGER),4) <> 0
                )
                -- 2월 30/31 제거
                AND NOT (
                    CAST(SUBSTRING(bt.res_treat_start_date,5,2) AS INTEGER) = 2
                    AND CAST(SUBSTRING(bt.res_treat_start_date,7,2) AS INTEGER) > 29
                )
                -- 4,6,9,11월 31일 제거
                AND NOT (
                    CAST(SUBSTRING(bt.res_treat_start_date,5,2) AS INTEGER) IN (4,6,9,11)
                    AND CAST(SUBSTRING(bt.res_treat_start_date,7,2) AS INTEGER) = 31
                )
                THEN to_date(bt.res_treat_start_date,'yyyyMMdd')
                ELSE NULL
            END
        ) AS first_obesity_date
    FROM basic_treatment bt
    WHERE (UPPER(bt.res_disease_code) LIKE 'E66%' OR bt.res_disease_name LIKE CONCAT('%', '{{ obesity_keyword }}', '%'))
        AND (bt.deleted IS NULL OR bt.deleted = FALSE)
    GROUP BY CAST(bt.user_id AS STRING)
),
hc_norm AS (
    -- 건강검진 미리보기 테이블 정규화: 날짜/ BMI 숫자화
    SELECT
        CAST(h.user_id AS STRING) AS user_id,
        -- 안전한 검진일 파싱
        CASE
            WHEN h.res_checkup_date RLIKE '^[0-9]{8}$'
            AND CAST(SUBSTRING(h.res_checkup_date,1,4) AS INTEGER) BETWEEN 1900 AND YEAR(current_date())
            AND CAST(SUBSTRING(h.res_checkup_date,5,2) AS INTEGER) BETWEEN 1 AND 12
            AND CAST(SUBSTRING(h.res_checkup_date,7,2) AS INTEGER) BETWEEN 1 AND 31
            AND NOT (
                CAST(SUBSTRING(h.res_checkup_date,5,2) AS INTEGER) = 2
                AND CAST(SUBSTRING(h.res_checkup_date,7,2) AS INTEGER) = 29
                AND MOD(CAST(SUBSTRING(h.res_checkup_date,1,4) AS INTEGER),4) <> 0
            )
            AND NOT (
                CAST(SUBSTRING(h.res_checkup_date,5,2) AS INTEGER) = 2
                AND CAST(SUBSTRING(h.res_checkup_date,7,2) AS INTEGER) > 29
            )
            AND NOT (
                CAST(SUBSTRING(h.res_checkup_date,5,2) AS INTEGER) IN (4,6,9,11)
                AND CAST(SUBSTRING(h.res_checkup_date,7,2) AS INTEGER) = 31
            )
            THEN to_date(h.res_checkup_date,'yyyyMMdd')
            ELSE NULL
        END AS checkup_date,
        -- BMI 숫자화 (문자/단위 제거)
        CAST(NULLIF(regexp_replace(h.res_bmi, '[^0-9\.]', ''), '') AS DOUBLE) AS bmi
    FROM nhis_health_checkup_preview h
),
hc_latest AS (
    -- 유저별 "가장 최근" 건강검진 한 건만 선택
    SELECT user_id, checkup_date, bmi
    FROM (
        SELECT
            user_id,
            checkup_date,
            bmi,
            ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY checkup_date DESC NULLS LAST) AS rn
        FROM hc_norm
        WHERE checkup_date IS NOT NULL
    )
    WHERE rn = 1
),
final_data AS (
    SELECT
        o.user_id,
        o.first_obesity_date,
        l.checkup_date AS latest_checkup_date,
        l.bmi,
        -- 아시아/대한비만학회 기준(권장): 과체중 23~24.9, 비만 ≥25
        CASE
            WHEN l.bmi IS NULL THEN 'UNKNOWN'
            WHEN l.bmi < 18.5 THEN 'UNDERWEIGHT'
            WHEN l.bmi < 23 THEN 'NORMAL'
            WHEN l.bmi < 25 THEN 'OVERWEIGHT(≥23)'
            WHEN l.bmi < 30 THEN 'OBESE I(≥25)'
            WHEN l.bmi < 35 THEN 'OBESE II(≥30)'
            ELSE 'OBESE III(≥35)'
        END AS bmi_category
    FROM obese_users o
    INNER JOIN hc_latest l
        ON o.user_id = l.user_id
)
SELECT
    bmi_category,
    COUNT(user_id) as patient_count
FROM final_data
GROUP BY bmi_category
ORDER BY
    CASE
        WHEN bmi_category = 'UNDERWEIGHT' THEN 1
        WHEN bmi_category = 'NORMAL' THEN 2
        WHEN bmi_category = 'OVERWEIGHT(≥23)' THEN 3
        WHEN bmi_category = 'OBESE I(≥25)' THEN 4
        WHEN bmi_category = 'OBESE II(≥30)' THEN 5
        WHEN bmi_category = 'OBESE III(≥35)' THEN 6
        ELSE 7
    END;