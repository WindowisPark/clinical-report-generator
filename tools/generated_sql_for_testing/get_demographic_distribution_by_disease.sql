-- Generated from: get_demographic_distribution_by_disease.yaml
-- Parameters used: {'disease_name_keyword': '당뇨병', 'start_date': '2022-01-01', 'end_date': '2024-12-31', 'snapshot_dt': '2025-09-01'}

-- 성별 분포 분석 (표준화 및 최적화)
-- 파라미터: disease_code_prefix = , start_date = 2022-01-01, end_date = 2024-12-31

-- 1단계: 환자별 한 번만 요약 (성능 최적화)
WITH patient_demographics AS (
    SELECT
        bt.user_id,
        MIN(bt.created_at) as first_visit,
        -- 성별 표준화: insured_person.gender 사용
        CASE
            WHEN ip.gender = 'MAN' THEN 'M'
            WHEN ip.gender = 'WOMAN' THEN 'F'
            WHEN ip.gender IN ('M', 'F') THEN ip.gender
            ELSE 'UNKNOWN'
        END as standardized_gender,
        u.birthday
    FROM basic_treatment bt
    JOIN user u ON bt.user_id = u.id
    LEFT JOIN insured_person ip ON bt.user_id = ip.user_id
    WHERE bt.res_disease_name LIKE '%당뇨병%'
        AND bt.created_at >= DATE '2022-01-01'
        AND bt.created_at < DATE '2024-12-31' + INTERVAL 1 DAY
        AND bt.deleted = false
        AND u.birthday IS NOT NULL
        AND LENGTH(u.birthday) >= 4
    GROUP BY bt.user_id, ip.gender, u.birthday
),
-- 2단계: first_visit 기준 연령 계산 (최적화)
patient_with_age AS (
    SELECT
        pd.user_id,
        pd.first_visit,
        pd.standardized_gender,
        -- first_visit 기준 연령 계산 (한 번만)
        YEAR(pd.first_visit) -
        CASE
            WHEN LENGTH(pd.birthday) >= 8 THEN CAST(SUBSTRING(pd.birthday, 1, 4) AS INT)
            WHEN LENGTH(pd.birthday) >= 6 THEN
                CASE
                    WHEN CAST(SUBSTRING(pd.birthday, 1, 2) AS INT) <= 30 THEN 2000 + CAST(SUBSTRING(pd.birthday, 1, 2) AS INT)
                    ELSE 1900 + CAST(SUBSTRING(pd.birthday, 1, 2) AS INT)
                END
            ELSE NULL
        END as age_at_first_visit
    FROM patient_demographics pd
),
-- 3단계: 연령대 분류
final_patient_data AS (
    SELECT
        pwa.*,
        CASE
            WHEN pwa.age_at_first_visit < 20 THEN '10대'
            WHEN pwa.age_at_first_visit < 30 THEN '20대'
            WHEN pwa.age_at_first_visit < 40 THEN '30대'
            WHEN pwa.age_at_first_visit < 50 THEN '40대'
            WHEN pwa.age_at_first_visit < 60 THEN '50대'
            ELSE '60대 이상'
        END as age_group
    FROM patient_with_age pwa
    WHERE pwa.age_at_first_visit IS NOT NULL
        AND pwa.age_at_first_visit BETWEEN 0 AND 120
)
-- 4단계: 최종 결과 (불필요한 윈도우 함수 제거)
SELECT
    '2-1. 성별 전체 분포 (표준화)' as analysis_type,
    standardized_gender as gender,
    COUNT(*) as patient_count,
    ROUND(AVG(age_at_first_visit), 1) as avg_age_at_first_visit,
    ROUND(TRY_DIVIDE(COUNT(*) * 100.0, SUM(COUNT(*)) OVER()), 2) as percentage,
    1 as sort_order
FROM final_patient_data
WHERE standardized_gender IN ('M', 'F')
GROUP BY standardized_gender

UNION ALL

-- 성별-연령대별 교차 분석 (서브쿼리 제거)
SELECT
    '2-2. 성별-연령대 교차분석' as analysis_type,
    CONCAT(standardized_gender, '-', age_group) as gender_age,
    COUNT(*) as patient_count,
    ROUND(AVG(age_at_first_visit), 1) as avg_age_at_first_visit,
    ROUND(TRY_DIVIDE(COUNT(*) * 100.0, (SELECT COUNT(*) FROM final_patient_data WHERE standardized_gender IN ('M', 'F'))), 2) as percentage,
    2 as sort_order
FROM final_patient_data
WHERE standardized_gender IN ('M', 'F')
GROUP BY standardized_gender, age_group

UNION ALL
-- UNKNOWN 성별 현황
SELECT
    '2-3. UNKNOWN 성별 현황' as analysis_type,
    'UNKNOWN' as gender_info,
    COUNT(*) as patient_count,
    ROUND(AVG(age_at_first_visit), 1) as avg_age_at_first_visit,
    ROUND(TRY_DIVIDE(COUNT(*) * 100.0, (SELECT COUNT(*) FROM final_patient_data)), 2) as percentage,
    3 as sort_order
FROM final_patient_data
WHERE standardized_gender = 'UNKNOWN'

ORDER BY sort_order, patient_count DESC;