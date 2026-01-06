-- 약물 중단율 생존분석 (치료클래스 + 위험요인)
-- 파라미터: disease_name_keyword = {{ disease_name_keyword }}, start_date = {{ start_date }}, end_date = {{ end_date }}, target_therapeutic_class = {{ target_therapeutic_class }}, analysis_period_days = {{ analysis_period_days }}

-- 1단계: 치료 클래스 정의
WITH therapeutic_classes AS (
    SELECT DISTINCT
        pd.res_ingredients,
        CASE
            WHEN pd.res_ingredients LIKE '%loxoprofen%' OR pd.res_ingredients LIKE '%diclofenac%' THEN 'NSAIDs'
            WHEN pd.res_ingredients LIKE '%rebamipide%' OR pd.res_ingredients LIKE '%sucralfate%' THEN 'GastroProtective'
            WHEN pd.res_ingredients LIKE '%acetaminophen%' THEN 'Analgesic'
            WHEN pd.res_ingredients LIKE '%mosapride%' OR pd.res_ingredients LIKE '%domperidone%' THEN 'Prokinetic'
            WHEN pd.res_ingredients LIKE '%chlorpheniramine%' THEN 'Antihistamine'
            ELSE 'Other'
        END as therapeutic_class
    FROM prescribed_drug pd
    WHERE pd.deleted = false
),
-- 2단계: 환자별 공변량 (위험요인) 계산
patient_covariates AS (
    SELECT
        bt.user_id,
        COUNT(DISTINCT bt.res_disease_code) as comorbidity_count,
        COUNT(DISTINCT pd.res_ingredients) as drug_class_count,
        COUNT(DISTINCT bt.res_hospital_code) as hospital_count,
        SUM(CAST(REGEXP_REPLACE(bt.res_total_amount, '[^0-9]', '') AS INTEGER)) as total_medical_cost,
        -- 위험요인 분류
        CASE
            WHEN COUNT(DISTINCT bt.res_disease_code) >= 3 THEN 'High_Comorbidity'
            WHEN COUNT(DISTINCT bt.res_disease_code) >= 2 THEN 'Medium_Comorbidity'
            ELSE 'Low_Comorbidity'
        END as comorbidity_level,
        CASE
            WHEN COUNT(DISTINCT pd.res_ingredients) >= 40 THEN 'High_Polypharmacy'
            WHEN COUNT(DISTINCT pd.res_ingredients) >= 20 THEN 'Medium_Polypharmacy'
            ELSE 'Low_Polypharmacy'
        END as polypharmacy_level,
        CASE
            WHEN SUM(CAST(REGEXP_REPLACE(bt.res_total_amount, '[^0-9]', '') AS INTEGER)) >= 100000000 THEN 'High_Cost'
            WHEN SUM(CAST(REGEXP_REPLACE(bt.res_total_amount, '[^0-9]', '') AS INTEGER)) >= 50000000 THEN 'Medium_Cost'
            ELSE 'Low_Cost'
        END as cost_category
    FROM basic_treatment bt
    JOIN prescribed_drug pd ON bt.user_id = pd.user_id
    WHERE bt.res_disease_name LIKE '%{{ disease_name_keyword }}%'
        AND bt.created_at >= '{{ start_date }}'
        AND bt.created_at <= '{{ end_date }}'
        AND bt.deleted = false
        AND pd.deleted = false
    GROUP BY bt.user_id
),
-- 3단계: 대상 치료클래스 처방 이력
target_prescriptions AS (
    SELECT
        pd.user_id,
        DATE(CONCAT(
            SUBSTRING(pd.res_treat_start_date, 1, 4), '-',
            SUBSTRING(pd.res_treat_start_date, 5, 2), '-',
            SUBSTRING(pd.res_treat_start_date, 7, 2)
        )) as prescription_date,
        CAST(pd.res_total_dosing_days AS INTEGER) as days_supply,
        ROW_NUMBER() OVER (PARTITION BY pd.user_id ORDER BY pd.res_treat_start_date) as prescription_order
    FROM prescribed_drug pd
    JOIN therapeutic_classes tc ON pd.res_ingredients = tc.res_ingredients
    WHERE tc.therapeutic_class = '{{ target_therapeutic_class }}'
        AND pd.res_total_dosing_days RLIKE '^[0-9]+$'
        AND CAST(pd.res_total_dosing_days AS INTEGER) > 0
        AND CAST(pd.res_total_dosing_days AS INTEGER) <= 180
        AND pd.deleted = false
),
-- 3.5단계: 최초 처방일 계산 (윈도우 함수 오류 수정)
with_initiation_date AS (
    SELECT
        user_id,
        prescription_date,
        days_supply,
        prescription_order,
        FIRST_VALUE(prescription_date) OVER (PARTITION BY user_id ORDER BY prescription_date) as first_prescription_date
    FROM target_prescriptions
),
-- 4단계: 중단 이벤트 식별 (Dynamic Gap 방식)
discontinuation_events AS (
    SELECT
        tp.user_id,
        tp.prescription_date as current_prescription,
        tp.days_supply as current_supply,
        LEAD(tp.prescription_date) OVER (PARTITION BY tp.user_id ORDER BY tp.prescription_date) as next_prescription,
        -- Dynamic Gap: 처방일수 + 30일 grace period
        DATE_ADD(tp.prescription_date, tp.days_supply + 30) as expected_next_prescription,
        CASE
            WHEN LEAD(tp.prescription_date) OVER (PARTITION BY tp.user_id ORDER BY tp.prescription_date) IS NULL THEN 1
            WHEN LEAD(tp.prescription_date) OVER (PARTITION BY tp.user_id ORDER BY tp.prescription_date) >
                 DATE_ADD(tp.prescription_date, tp.days_supply + 30) THEN 1
            ELSE 0
        END as discontinuation_flag,
        -- 치료 지속 기간 계산
        DATEDIFF(tp.prescription_date, tp.first_prescription_date) as days_from_initiation,
        -- 공변량 추가
        pc.comorbidity_level,
        pc.polypharmacy_level,
        pc.cost_category,
        pc.comorbidity_count,
        pc.drug_class_count
    FROM with_initiation_date tp
    LEFT JOIN patient_covariates pc ON tp.user_id = pc.user_id
    WHERE DATEDIFF(tp.prescription_date, tp.first_prescription_date) <= {{ analysis_period_days }}
)

-- 최종 결과: 생존분석 + 위험요인별 중단율
SELECT
    '약물 중단율 생존분석' as analysis_type,
    CASE
        WHEN days_from_initiation <= 30 THEN '0-30일'
        WHEN days_from_initiation <= 60 THEN '31-60일'
        WHEN days_from_initiation <= 90 THEN '61-90일'
        WHEN days_from_initiation <= 180 THEN '91-180일'
        ELSE '180일+'
    END as time_period,
    comorbidity_level,
    polypharmacy_level,
    cost_category,
    COUNT(*) as total_prescriptions,
    SUM(discontinuation_flag) as discontinuation_events,
    ROUND(SUM(discontinuation_flag) * 100.0 / COUNT(*), 2) as discontinuation_rate,
    COUNT(DISTINCT user_id) as unique_patients,
    ROUND(AVG(comorbidity_count), 1) as avg_comorbidities,
    ROUND(AVG(drug_class_count), 1) as avg_drug_classes,
    -- 위험비 계산 (reference: Low_Comorbidity, Low_Polypharmacy, Low_Cost)
    CASE
        WHEN comorbidity_level = 'High_Comorbidity' OR polypharmacy_level = 'High_Polypharmacy' OR cost_category = 'High_Cost'
        THEN '고위험군'
        WHEN comorbidity_level = 'Medium_Comorbidity' OR polypharmacy_level = 'Medium_Polypharmacy' OR cost_category = 'Medium_Cost'
        THEN '중위험군'
        ELSE '저위험군'
    END as risk_group
FROM discontinuation_events
WHERE comorbidity_level IS NOT NULL  -- 공변량이 있는 환자만
GROUP BY time_period, comorbidity_level, polypharmacy_level, cost_category
ORDER BY
    CASE
        WHEN time_period = '0-30일' THEN 1
        WHEN time_period = '31-60일' THEN 2
        WHEN time_period = '61-90일' THEN 3
        WHEN time_period = '91-180일' THEN 4
        ELSE 5
    END,
    discontinuation_rate DESC;