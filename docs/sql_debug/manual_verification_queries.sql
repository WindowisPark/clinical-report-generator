-- =================================================================
-- 수기 검증용 쿼리 모음
-- =================================================================

-- =================================================================
-- 1. 고혈압 환자의 복약 순응도 검증
-- =================================================================

-- 1-1. 고혈압 환자 기본 통계
SELECT
    '1-1. 고혈압 환자 기본 통계' as verification_step,
    COUNT(DISTINCT bt.user_id) as total_hypertension_patients,
    MIN(bt.res_treat_start_date) as earliest_treatment,
    MAX(bt.res_treat_start_date) as latest_treatment
FROM basic_treatment bt
WHERE bt.res_disease_name LIKE '%고혈압%'
    AND bt.res_treat_start_date >= '2022-01-01'
    AND bt.res_treat_start_date <= '2024-12-31'
    AND bt.deleted = false;

-- 1-2. 고혈압 환자의 처방 데이터 존재 여부
SELECT
    '1-2. 고혈압 환자 처방 데이터' as verification_step,
    COUNT(DISTINCT pd.user_id) as patients_with_prescriptions,
    COUNT(*) as total_prescriptions,
    COUNT(CASE WHEN pd.res_ingredients IS NOT NULL AND pd.res_ingredients != '' THEN 1 END) as prescriptions_with_ingredients
FROM prescribed_drug pd
JOIN (
    SELECT DISTINCT bt.user_id
    FROM basic_treatment bt
    WHERE bt.res_disease_name LIKE '%고혈압%'
        AND bt.res_treat_start_date >= '2022-01-01'
        AND bt.res_treat_start_date <= '2024-12-31'
        AND bt.deleted = false
) hyper_patients ON pd.user_id = hyper_patients.user_id
WHERE pd.deleted = false;

-- 1-3. 고혈압 환자의 주요 처방 성분 TOP 10
SELECT
    '1-3. 주요 처방 성분' as verification_step,
    pd.res_ingredients,
    COUNT(DISTINCT pd.user_id) as patient_count,
    COUNT(*) as prescription_count
FROM prescribed_drug pd
JOIN (
    SELECT DISTINCT bt.user_id
    FROM basic_treatment bt
    WHERE bt.res_disease_name LIKE '%고혈압%'
        AND bt.res_treat_start_date >= '2022-01-01'
        AND bt.res_treat_start_date <= '2024-12-31'
        AND bt.deleted = false
) hyper_patients ON pd.user_id = hyper_patients.user_id
WHERE pd.deleted = false
    AND pd.res_ingredients IS NOT NULL
    AND pd.res_ingredients != ''
GROUP BY pd.res_ingredients
ORDER BY patient_count DESC
LIMIT 10;

-- 1-4. 투약일수 데이터 품질 검증
SELECT
    '1-4. 투약일수 데이터 품질' as verification_step,
    COUNT(*) as total_prescriptions,
    COUNT(CASE WHEN pd.res_total_dosing_days IS NOT NULL AND pd.res_total_dosing_days != '' THEN 1 END) as has_dosing_days,
    COUNT(CASE WHEN pd.res_total_dosing_days REGEXP '^[0-9]+$' THEN 1 END) as valid_numeric_days,
    COUNT(CASE WHEN pd.res_total_dosing_days REGEXP '^[0-9]+$'
               AND CAST(pd.res_total_dosing_days AS INT) > 0
               AND CAST(pd.res_total_dosing_days AS INT) <= 180 THEN 1 END) as reasonable_dosing_days
FROM prescribed_drug pd
JOIN (
    SELECT DISTINCT bt.user_id
    FROM basic_treatment bt
    WHERE bt.res_disease_name LIKE '%고혈압%'
        AND bt.res_treat_start_date >= '2022-01-01'
        AND bt.res_treat_start_date <= '2024-12-31'
        AND bt.deleted = false
) hyper_patients ON pd.user_id = hyper_patients.user_id
WHERE pd.deleted = false;

-- =================================================================
-- 2. 고혈압 환자의 병원 등급별 분포 검증
-- =================================================================

-- 2-1. 병원 데이터 기본 통계
SELECT
    '2-1. 병원 데이터 기본 통계' as verification_step,
    COUNT(*) as total_hospitals,
    COUNT(CASE WHEN sido_name IS NOT NULL AND sido_name != '' THEN 1 END) as has_sido,
    COUNT(CASE WHEN medical_facility_type_code IS NOT NULL AND medical_facility_type_code != '' THEN 1 END) as has_facility_type
FROM hospital;

-- 2-2. 의료기관 종류별 분포
SELECT
    '2-2. 의료기관 종류별 분포' as verification_step,
    h.medical_facility_type_code as facility_type,
    COUNT(*) as hospital_count
FROM hospital h
WHERE h.medical_facility_type_code IS NOT NULL
    AND h.medical_facility_type_code != ''
GROUP BY h.medical_facility_type_code
ORDER BY hospital_count DESC;

-- 2-3. 고혈압 환자의 병원 등급별 방문 분포
SELECT
    '2-3. 고혈압 환자 병원 등급별 분포' as verification_step,
    CASE
        WHEN h.medical_facility_type_code LIKE '%상급종합%' THEN '상급종합병원'
        WHEN h.medical_facility_type_code LIKE '%종합%' THEN '종합병원'
        WHEN h.medical_facility_type_code LIKE '%의원%' THEN '의원'
        WHEN h.medical_facility_type_code LIKE '%병원%' THEN '병원'
        ELSE COALESCE(h.medical_facility_type_code, '미분류')
    END as hospital_tier,
    COUNT(DISTINCT bt.user_id) as unique_patients,
    COUNT(*) as total_visits,
    ROUND(COUNT(DISTINCT bt.user_id) * 100.0 / SUM(COUNT(DISTINCT bt.user_id)) OVER(), 2) as patient_percentage
FROM basic_treatment bt
LEFT JOIN hospital h ON bt.res_hospital_code = h.hospital_code
WHERE bt.res_disease_name LIKE '%고혈압%'
    AND bt.res_treat_start_date >= '2022-01-01'
    AND bt.res_treat_start_date <= '2024-12-31'
    AND bt.deleted = false
GROUP BY hospital_tier
ORDER BY unique_patients DESC;

-- =================================================================
-- 3. Recruitment Feasibility 검증
-- =================================================================

-- 3-1. 전체 고혈압 환자 풀
SELECT
    '3-1. 전체 고혈압 환자 풀' as verification_step,
    COUNT(DISTINCT bt.user_id) as total_pool_patients
FROM basic_treatment bt
JOIN user u ON bt.user_id = u.id
WHERE bt.res_disease_name LIKE '%고혈압%'
    AND bt.res_treat_start_date >= '2022-01-01'
    AND bt.res_treat_start_date <= '2024-12-31'
    AND bt.deleted = false
    AND u.birthday IS NOT NULL
    AND LENGTH(u.birthday) >= 4;

-- 3-2. 연령별 분포 (성인 범위 확인)
SELECT
    '3-2. 연령별 분포' as verification_step,
    CASE
        WHEN age < 18 THEN '미성년'
        WHEN age BETWEEN 18 AND 65 THEN '성인'
        WHEN age > 65 THEN '고령자'
        ELSE '연령미상'
    END as age_group,
    COUNT(DISTINCT user_id) as patient_count
FROM (
    SELECT DISTINCT
        bt.user_id,
        YEAR(CURRENT_DATE()) -
        CASE
            WHEN LENGTH(u.birthday) >= 8 THEN TRY_CAST(SUBSTRING(u.birthday, 1, 4) AS INT)
            WHEN LENGTH(u.birthday) >= 6 THEN
                CASE WHEN TRY_CAST(SUBSTRING(u.birthday, 1, 2) AS INT) <= 30
                     THEN 2000 + TRY_CAST(SUBSTRING(u.birthday, 1, 2) AS INT)
                     ELSE 1900 + TRY_CAST(SUBSTRING(u.birthday, 1, 2) AS INT)
                END
            ELSE NULL
        END as age
    FROM basic_treatment bt
    JOIN user u ON bt.user_id = u.id
    WHERE bt.res_disease_name LIKE '%고혈압%'
        AND bt.res_treat_start_date >= '2022-01-01'
        AND bt.res_treat_start_date <= '2024-12-31'
        AND bt.deleted = false
        AND u.birthday IS NOT NULL
        AND LENGTH(u.birthday) >= 4
) age_calc
GROUP BY age_group
ORDER BY patient_count DESC;

-- 3-3. 방문 횟수별 분포
SELECT
    '3-3. 방문 횟수별 분포' as verification_step,
    CASE
        WHEN visit_count = 1 THEN '1회 방문'
        WHEN visit_count BETWEEN 2 AND 5 THEN '2-5회 방문'
        WHEN visit_count BETWEEN 6 AND 10 THEN '6-10회 방문'
        WHEN visit_count > 10 THEN '10회 초과'
    END as visit_frequency,
    COUNT(*) as patient_count
FROM (
    SELECT
        bt.user_id,
        COUNT(*) as visit_count
    FROM basic_treatment bt
    WHERE bt.res_disease_name LIKE '%고혈압%'
        AND bt.res_treat_start_date >= '2022-01-01'
        AND bt.res_treat_start_date <= '2024-12-31'
        AND bt.deleted = false
    GROUP BY bt.user_id
) visit_stats
GROUP BY visit_frequency
ORDER BY patient_count DESC;

-- 3-4. 최종 모집 자격 요건 시뮬레이션 (19-65, 최소 1회 방문)
SELECT
    '3-4. 모집 자격 시뮬레이션' as verification_step,
    COUNT(DISTINCT bt.user_id) as total_pool,
    COUNT(DISTINCT CASE WHEN age BETWEEN 19 AND 65 THEN bt.user_id END) as adult_qualified,
    COUNT(DISTINCT CASE WHEN visit_count >= 1 THEN bt.user_id END) as visit_qualified,
    COUNT(DISTINCT CASE WHEN age BETWEEN 19 AND 65 AND visit_count >= 1 THEN bt.user_id END) as fully_qualified,
    ROUND(COUNT(DISTINCT CASE WHEN age BETWEEN 19 AND 65 AND visit_count >= 1 THEN bt.user_id END) * 100.0 / 200, 2) as target_ratio_200
FROM (
    SELECT
        bt.user_id,
        YEAR(CURRENT_DATE()) -
        CASE
            WHEN LENGTH(u.birthday) >= 8 THEN TRY_CAST(SUBSTRING(u.birthday, 1, 4) AS INT)
            WHEN LENGTH(u.birthday) >= 6 THEN
                CASE WHEN TRY_CAST(SUBSTRING(u.birthday, 1, 2) AS INT) <= 30
                     THEN 2000 + TRY_CAST(SUBSTRING(u.birthday, 1, 2) AS INT)
                     ELSE 1900 + TRY_CAST(SUBSTRING(u.birthday, 1, 2) AS INT)
                END
            ELSE NULL
        END as age,
        COUNT(*) as visit_count
    FROM basic_treatment bt
    JOIN user u ON bt.user_id = u.id
    WHERE bt.res_disease_name LIKE '%고혈압%'
        AND bt.res_treat_start_date >= '2022-01-01'
        AND bt.res_treat_start_date <= '2024-12-31'
        AND bt.deleted = false
        AND u.birthday IS NOT NULL
        AND LENGTH(u.birthday) >= 4
    GROUP BY bt.user_id, u.birthday
) qualified_check
JOIN basic_treatment bt ON qualified_check.user_id = bt.user_id
WHERE bt.res_disease_name LIKE '%고혈압%'
    AND bt.res_treat_start_date >= '2022-01-01'
    AND bt.res_treat_start_date <= '2024-12-31'
    AND bt.deleted = false;