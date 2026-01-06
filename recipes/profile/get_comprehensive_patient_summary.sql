-- 특정 질환 코드와 기간에 해당하는 환자군의 종합 현황 분석
-- 파라미터: disease_name_keyword = {{ disease_name_keyword }}, start_date = {{ start_date }}, end_date = {{ end_date }}, hospital_type_filter = {{ hospital_type_filter }}

WITH patient_base AS (
    SELECT DISTINCT
        bt.user_id,
        bt.res_disease_code,
        bt.res_disease_name,
        bt.res_total_amount,
        bt.res_department,
        bt.res_hospital_code,
        u.birthday,
        YEAR(CURRENT_DATE()) -
        CASE
            WHEN LENGTH(u.birthday) >= 8 THEN CAST(SUBSTRING(u.birthday, 1, 4) AS INTEGER)
            WHEN LENGTH(u.birthday) >= 6 THEN
                CASE
                    WHEN CAST(SUBSTRING(u.birthday, 1, 2) AS INTEGER) <= 30 THEN 2000 + CAST(SUBSTRING(u.birthday, 1, 2) AS INTEGER)
                    ELSE 1900 + CAST(SUBSTRING(u.birthday, 1, 2) AS INTEGER)
                END
            ELSE NULL
        END as age
    FROM basic_treatment bt
    JOIN user u ON bt.user_id = u.id
    WHERE bt.res_disease_name LIKE '%{{ disease_name_keyword }}%'
        AND bt.res_treat_start_date >= '{{ start_date }}'
        AND bt.res_treat_start_date <= '{{ end_date }}'
        AND bt.deleted = false
        AND u.birthday IS NOT NULL
        AND LENGTH(u.birthday) >= 4
),
patient_profile AS (
    SELECT
        pb.*,
        h.sido_name,
        h.sigungu_name,
        h.medical_facility_type_code,
        COUNT(*) OVER (PARTITION BY pb.user_id) as total_visits
    FROM patient_base pb
    JOIN hospital h ON pb.res_hospital_code = h.hospital_code
    WHERE h.sido_name != ''
        {% if hospital_type_filter %}
        AND h.medical_facility_type_code LIKE '%{{ hospital_type_filter }}%'
        {% endif %}
)

SELECT
    '1. 종합 환자 현황' as analysis_type,
    COUNT(DISTINCT user_id) as total_unique_patients,
    COUNT(*) as total_treatments,
    ROUND(AVG(CAST(REGEXP_REPLACE(res_total_amount, '[^0-9]', '') AS DECIMAL)), 0) as avg_treatment_cost,
    ROUND(AVG(age), 1) as avg_age,
    ROUND(AVG(total_visits), 1) as avg_visits_per_patient
FROM patient_profile;