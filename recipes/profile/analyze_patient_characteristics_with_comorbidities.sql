-- MASH 환자 특성 분석 (연령, 합병증, 병원 분포)
-- 파라미터: disease_keyword = {{ disease_keyword }}

WITH mash_patients AS (
    SELECT
        bt.user_id,
        MIN(bt.res_treat_start_date) AS first_treat_date,
        MAX(bt.res_treat_start_date) AS last_treat_date
    FROM basic_treatment bt
    WHERE bt.res_disease_name LIKE CONCAT('%', '{{ disease_keyword }}', '%')
        AND bt.res_treat_start_date RLIKE '^[0-9]{8}$'
        AND bt.deleted = FALSE
    GROUP BY bt.user_id
),
with_age AS (
    SELECT
        m.user_id,
        m.first_treat_date,
        m.last_treat_date,
        CAST(ip.birthday AS STRING) AS birthday_str,
        CASE
            WHEN ip.birthday RLIKE '^[0-9]{8}$'
            THEN FLOOR(DATEDIFF(to_date(m.first_treat_date, 'yyyyMMdd'), to_date(ip.birthday, 'yyyyMMdd')) / 365.25)
            ELSE NULL
        END AS age_at_first_diagnosis
    FROM mash_patients m
    LEFT JOIN insured_person ip
        ON m.user_id = ip.user_id
),
with_comorb AS (
    SELECT
        a.user_id,
        a.age_at_first_diagnosis,
        a.first_treat_date,
        a.last_treat_date,
        -- 합병증 동반 여부 플래그
        MAX(CASE WHEN bt.res_disease_code LIKE 'E11%' OR bt.res_disease_name LIKE '%{{ t2d_keyword }}%' THEN 1 ELSE 0 END) AS has_t2d,
        MAX(CASE WHEN bt.res_disease_code LIKE 'E78%' OR bt.res_disease_name LIKE '%{{ dyslipidemia_keyword }}%' OR bt.res_disease_name LIKE '%고지혈%' THEN 1 ELSE 0 END) AS has_dyslipidemia,
        MAX(CASE WHEN bt.res_disease_code LIKE 'I10%' OR bt.res_disease_name LIKE '%{{ hypertension_keyword }}%' THEN 1 ELSE 0 END) AS has_hypertension
    FROM with_age a
    LEFT JOIN basic_treatment bt
        ON a.user_id = bt.user_id
        AND bt.res_treat_start_date BETWEEN a.first_treat_date AND a.last_treat_date
        AND bt.deleted = FALSE
    GROUP BY a.user_id, a.age_at_first_diagnosis, a.first_treat_date, a.last_treat_date
),
with_hospital AS (
    SELECT
        c.user_id,
        c.age_at_first_diagnosis,
        c.has_t2d,
        c.has_dyslipidemia,
        c.has_hypertension,
        -- 병원 등급 매핑
        CASE
            WHEN h.medical_facility_type_code IN ('01','1') THEN '3차'
            WHEN h.medical_facility_type_code IN ('11','21','28','29','41','92') THEN '2차'
            ELSE '1차'
        END AS hospital_level
    FROM with_comorb c
    LEFT JOIN basic_treatment bt
        ON c.user_id = bt.user_id
        AND bt.res_disease_name LIKE CONCAT('%', '{{ disease_keyword }}', '%')
        AND bt.deleted = FALSE
    LEFT JOIN hospital h
        ON bt.res_hospital_code = h.hospital_code
),
hospital_mode AS (
    -- 각 유저별 최빈 병원등급 산출
    SELECT
        user_id,
        MAX_BY(hospital_level, cnt) AS main_hospital_level
    FROM (
        SELECT
            user_id,
            hospital_level,
            COUNT(*) AS cnt
        FROM with_hospital
        WHERE hospital_level IS NOT NULL
        GROUP BY user_id, hospital_level
    ) t
    GROUP BY user_id
)

SELECT
    w.user_id,
    w.age_at_first_diagnosis,
    w.has_t2d,
    w.has_dyslipidemia,
    w.has_hypertension,
    hm.main_hospital_level
FROM with_hospital w
LEFT JOIN hospital_mode hm
    ON w.user_id = hm.user_id
GROUP BY w.user_id, w.age_at_first_diagnosis, w.has_t2d, w.has_dyslipidemia, w.has_hypertension, hm.main_hospital_level;