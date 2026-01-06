-- 환자 정보(마스킹), 진단, 약물 정보 통합 조회 쿼리
-- 개인식별정보는 마스킹 처리하고 약물 코드까지 포함

WITH patient_basic_info AS (
    -- 환자 기본 정보 (마스킹 처리)
    SELECT
        ip.user_id,
        CONCAT('PATIENT_', LPAD(ip.user_id, 8, '0')) AS masked_patient_id,
        ip.gender,
        -- 나이 계산 (간단하게 처리)
        CASE
            WHEN ip.birthday IS NOT NULL AND LENGTH(ip.birthday) >= 8
                 AND TRY_CAST(SUBSTRING(ip.birthday, 1, 4) AS INT) IS NOT NULL
                 AND TRY_CAST(SUBSTRING(ip.birthday, 1, 4) AS INT) > 1900 THEN
                YEAR(CURRENT_DATE()) - TRY_CAST(SUBSTRING(ip.birthday, 1, 4) AS INT)
            WHEN ip.birthday IS NOT NULL AND LENGTH(ip.birthday) >= 6
                 AND TRY_CAST(SUBSTRING(ip.birthday, 1, 2) AS INT) IS NOT NULL THEN
                CASE
                    WHEN TRY_CAST(SUBSTRING(ip.birthday, 1, 2) AS INT) <= 30 THEN
                        YEAR(CURRENT_DATE()) - (2000 + TRY_CAST(SUBSTRING(ip.birthday, 1, 2) AS INT))
                    ELSE
                        YEAR(CURRENT_DATE()) - (1900 + TRY_CAST(SUBSTRING(ip.birthday, 1, 2) AS INT))
                END
            ELSE NULL
        END as age
    FROM insured_person ip
    WHERE ip.birthday IS NOT NULL
        AND LENGTH(ip.birthday) >= 4
),

patient_with_age_group AS (
    -- 나이대 그룹 계산 (별도 CTE로 분리)
    SELECT
        user_id,
        masked_patient_id,
        gender,
        age,
        CASE
            WHEN age IS NOT NULL AND age >= 0 AND age < 20 THEN '10대'
            WHEN age IS NOT NULL AND age >= 20 AND age < 30 THEN '20대'
            WHEN age IS NOT NULL AND age >= 30 AND age < 40 THEN '30대'
            WHEN age IS NOT NULL AND age >= 40 AND age < 50 THEN '40대'
            WHEN age IS NOT NULL AND age >= 50 AND age < 60 THEN '50대'
            WHEN age IS NOT NULL AND age >= 60 AND age < 70 THEN '60대'
            WHEN age IS NOT NULL AND age >= 70 THEN '70대 이상'
            ELSE '미상'
        END as age_group
    FROM patient_basic_info
),

diagnosis_info AS (
    -- 진단 정보
    SELECT
        bt.user_id,
        bt.res_treat_start_date as treatment_date,
        bt.res_hospital_name as hospital_name,
        bt.res_department as department,
        bt.res_disease_code as diagnosis_code,
        bt.res_disease_name as diagnosis_name,
        bt.res_total_amount as treatment_cost,
        ROW_NUMBER() OVER (PARTITION BY bt.user_id ORDER BY bt.res_treat_start_date DESC) as rn
    FROM basic_treatment bt
    WHERE bt.deleted = false
        AND bt.res_disease_name IS NOT NULL
        AND bt.res_disease_name != ''
),

medication_info AS (
    -- 약물 정보 (약물 코드 포함)
    SELECT
        pd.user_id,
        pd.res_treat_start_date as prescription_date,
        pd.res_hospital_name as prescribing_hospital,
        pd.res_drug_name as drug_name,
        pd.res_ingredients as drug_ingredients,
        pd.res_one_dose as dosage_per_time,
        pd.res_daily_doses_number as daily_frequency,
        pd.res_total_dosing_days as total_dosing_days,
        ROW_NUMBER() OVER (PARTITION BY pd.user_id ORDER BY pd.res_treat_start_date DESC) as rn
    FROM prescribed_drug pd
    WHERE pd.deleted = false
        AND pd.res_drug_name IS NOT NULL
        AND pd.res_drug_name != ''
),

drug_code_info AS (
    -- 약물 코드 정보 (detail_treatment 테이블에서)
    SELECT
        dt.user_id,
        dt.res_code_name as medication_code,
        dt.res_treat_type as treatment_type,
        dt.res_one_dose as dosage_per_time_detail,
        dt.res_daily_doses_number as daily_frequency_detail,
        dt.res_total_dosing_days as total_dosing_days_detail,
        ROW_NUMBER() OVER (PARTITION BY dt.user_id ORDER BY dt.created_at DESC) as rn
    FROM detail_treatment dt
    WHERE dt.deleted = false
        AND dt.res_code_name IS NOT NULL
        AND dt.res_code_name != ''
)

-- 최종 결과: 환자별 최신 진단 및 처방 정보 조회
SELECT
    pbi.masked_patient_id,
    pbi.gender,
    pbi.age,
    pbi.age_group,

    -- 진단 정보
    di.treatment_date,
    di.hospital_name,
    di.department,
    di.diagnosis_code,
    di.diagnosis_name,
    di.treatment_cost,

    -- 약물 정보
    mi.prescription_date,
    mi.prescribing_hospital,
    mi.drug_name,
    mi.drug_ingredients,
    mi.dosage_per_time,
    mi.daily_frequency,
    mi.total_dosing_days,

    -- 약물 코드 정보
    dci.medication_code,
    dci.treatment_type,

    -- 추가 지표
    CASE
        WHEN di.treatment_date = mi.prescription_date THEN 'SAME_DAY'
        WHEN ABS(DATEDIFF(TO_DATE(di.treatment_date, 'yyyyMMdd'), TO_DATE(mi.prescription_date, 'yyyyMMdd'))) <= 3 THEN 'WITHIN_3_DAYS'
        ELSE 'DIFFERENT_PERIOD'
    END as treatment_prescription_match

FROM patient_with_age_group pbi
LEFT JOIN diagnosis_info di ON pbi.user_id = di.user_id AND di.rn = 1
LEFT JOIN medication_info mi ON pbi.user_id = mi.user_id AND mi.rn = 1
LEFT JOIN drug_code_info dci ON pbi.user_id = dci.user_id AND dci.rn = 1

-- 실제 데이터가 있는 환자만 조회
WHERE di.user_id IS NOT NULL
   OR mi.user_id IS NOT NULL

ORDER BY pbi.user_id
LIMIT 100;  -- 샘플 데이터로 100명만 조회