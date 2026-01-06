-- 병원 이름 데이터 확인용 쿼리

-- 1. hospital.name 컬럼 샘플 확인
SELECT
    'hospital.name 샘플' as debug_step,
    h.name as hospital_name,
    COUNT(*) as count_hospitals
FROM hospital h
WHERE h.name IS NOT NULL
    AND h.name != ''
GROUP BY h.name
ORDER BY count_hospitals DESC
LIMIT 20;

-- 2. 고혈압 환자가 이용하는 병원명 샘플
SELECT
    '고혈압 환자 이용 병원명' as debug_step,
    h.name as hospital_name,
    COUNT(DISTINCT bt.user_id) as unique_patients,
    COUNT(*) as total_visits
FROM basic_treatment bt
LEFT JOIN hospital h ON bt.res_hospital_code = h.hospital_code
WHERE bt.deleted = FALSE
    AND bt.res_disease_name LIKE '%고혈압%'
    AND bt.res_treat_start_date >= '2022-01-01'
    AND bt.res_treat_start_date <= '2024-12-31'
    AND h.name IS NOT NULL
    AND h.name != ''
GROUP BY h.name
ORDER BY unique_patients DESC
LIMIT 20;

-- 3. hospital_code vs name 매칭 확인
SELECT
    'hospital_code vs name' as debug_step,
    bt.res_hospital_code,
    h.name as hospital_name,
    h.medical_facility_type_code,
    COUNT(DISTINCT bt.user_id) as unique_patients
FROM basic_treatment bt
LEFT JOIN hospital h ON bt.res_hospital_code = h.hospital_code
WHERE bt.deleted = FALSE
    AND bt.res_disease_name LIKE '%고혈압%'
    AND bt.res_treat_start_date >= '2022-01-01'
    AND bt.res_treat_start_date <= '2024-12-31'
GROUP BY bt.res_hospital_code, h.name, h.medical_facility_type_code
ORDER BY unique_patients DESC
LIMIT 15;

-- 4. res_hospital_name vs hospital.name 비교
SELECT
    'res_hospital_name vs hospital.name' as debug_step,
    bt.res_hospital_name as treatment_hospital_name,
    h.name as master_hospital_name,
    COUNT(DISTINCT bt.user_id) as unique_patients
FROM basic_treatment bt
LEFT JOIN hospital h ON bt.res_hospital_code = h.hospital_code
WHERE bt.deleted = FALSE
    AND bt.res_disease_name LIKE '%고혈압%'
    AND bt.res_treat_start_date >= '2022-01-01'
    AND bt.res_treat_start_date <= '2024-12-31'
GROUP BY bt.res_hospital_name, h.name
ORDER BY unique_patients DESC
LIMIT 15;