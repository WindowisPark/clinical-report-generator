-- Generated from: get_comprehensive_patient_summary.yaml
-- Parameters used: {'disease_name_keyword': '당뇨병', 'start_date': '2022-01-01', 'end_date': '2024-12-31', 'hospital_type_filter': 'test_string', 'snapshot_dt': '2025-09-01'}

-- 특정 질환 코드와 기간에 해당하는 환자군의 종합 현황 분석
-- 파라미터: disease_code_prefix = , start_date = 2022-01-01, end_date = 2024-12-31

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
            WHEN LENGTH(u.birthday) >= 8 THEN CAST(SUBSTRING(u.birthday, 1, 4) AS INT)
            WHEN LENGTH(u.birthday) >= 6 THEN
                CASE
                    WHEN CAST(SUBSTRING(u.birthday, 1, 2) AS INT) <= 30 THEN 2000 + CAST(SUBSTRING(u.birthday, 1, 2) AS INT)
                    ELSE 1900 + CAST(SUBSTRING(u.birthday, 1, 2) AS INT)
                END
            ELSE NULL
        END as age
    FROM basic_treatment bt
    JOIN user u ON bt.user_id = u.id
    WHERE bt.res_disease_name LIKE '%당뇨병%'
        AND bt.created_at >= '2022-01-01'
        AND bt.created_at <= '2024-12-31'
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
        
        AND h.medical_facility_type_code LIKE '%test_string%'
        
)

SELECT
    '1. 종합 환자 현황' as analysis_type,
    COUNT(DISTINCT user_id) as total_unique_patients,
    COUNT(*) as total_treatments,
    ROUND(AVG(CAST(REGEXP_REPLACE(res_total_amount, '[^0-9]', '') AS DECIMAL)), 0) as avg_treatment_cost,
    ROUND(AVG(age), 1) as avg_age,
    ROUND(AVG(total_visits), 1) as avg_visits_per_patient
FROM patient_profile;