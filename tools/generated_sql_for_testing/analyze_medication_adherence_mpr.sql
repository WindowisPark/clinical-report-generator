-- Generated from: analyze_medication_adherence_mpr.yaml
-- Parameters used: {'disease_name_keyword': '당뇨병', 'start_date': '2022-01-01', 'end_date': '2024-12-31', 'target_ingredient': '아스피린', 'analysis_period_days': 365, 'snapshot_dt': '2025-09-01'}

-- MPR 복약순응도 지표 계산 분석
-- 파라미터: disease_name_keyword = 당뇨병, start_date = 2022-01-01, end_date = 2024-12-31, target_ingredient = 아스피린, analysis_period_days = 365

-- 1단계: 대상 환자 및 최초 진단일 수집
WITH target_patients AS (
    SELECT DISTINCT
        bt.user_id,
        MIN(DATE(bt.created_at)) as first_diagnosis_date
    FROM basic_treatment bt
    WHERE bt.res_disease_name LIKE '%당뇨병%'
        AND bt.created_at >= '2022-01-01'
        AND bt.created_at <= '2024-12-31'
        AND bt.deleted = false
    GROUP BY bt.user_id
),
-- 2단계: 대상 약물 처방 정보 수집
medication_prescriptions AS (
    SELECT
        pd.user_id,
        DATE(CONCAT(
            SUBSTRING(pd.res_treat_start_date, 1, 4), '-',
            SUBSTRING(pd.res_treat_start_date, 5, 2), '-',
            SUBSTRING(pd.res_treat_start_date, 7, 2)
        )) as prescription_date,
        pd.res_drug_name,
        pd.res_ingredients,
        CAST(pd.res_total_dosing_days AS INT) as days_supply
    FROM prescribed_drug pd
    JOIN target_patients tp ON pd.user_id = tp.user_id
    WHERE pd.res_ingredients LIKE '%아스피린%'
        AND pd.res_total_dosing_days REGEXP '^[0-9]+$'
        AND CAST(pd.res_total_dosing_days AS INT) > 0
        AND CAST(pd.res_total_dosing_days AS INT) <= 180  -- 합리적 범위 제한
        AND pd.deleted = false
),
-- 3단계: 환자별 분석 기간 설정
patient_analysis_periods AS (
    SELECT
        tp.user_id,
        tp.first_diagnosis_date,
        tp.first_diagnosis_date as analysis_start_date,
        tp.first_diagnosis_date + INTERVAL '365' DAY as analysis_end_date,
        365 as total_analysis_days
    FROM target_patients tp
),
-- 4단계: MPR 계산 (Medication Possession Ratio)
mpr_calculations AS (
    SELECT
        pap.user_id,
        pap.analysis_start_date,
        pap.analysis_end_date,
        pap.total_analysis_days,
        COUNT(mp.prescription_date) as total_prescriptions,
        SUM(mp.days_supply) as total_days_supplied,
        -- MPR = (총 처방된 일수) / (분석 기간 일수) × 100
        ROUND(SUM(mp.days_supply) * 100.0 / pap.total_analysis_days, 2) as mpr_percentage,
        MIN(mp.prescription_date) as first_prescription_date,
        MAX(mp.prescription_date) as last_prescription_date
    FROM patient_analysis_periods pap
    LEFT JOIN medication_prescriptions mp ON pap.user_id = mp.user_id
        AND mp.prescription_date >= pap.analysis_start_date
        AND mp.prescription_date <= pap.analysis_end_date
    GROUP BY pap.user_id, pap.analysis_start_date, pap.analysis_end_date, pap.total_analysis_days
    HAVING COUNT(mp.prescription_date) > 0  -- 처방 이력이 있는 환자만
)

-- 최종 결과: MPR 복약순응도 통계 요약
SELECT
    'MPR 복약순응도 분석' as analysis_type,
    CASE
        WHEN mpr_percentage >= 80 THEN '우수한_순응도_(≥80%)'
        WHEN mpr_percentage >= 60 THEN '보통_순응도_(60-79%)'
        WHEN mpr_percentage >= 40 THEN '불량한_순응도_(40-59%)'
        ELSE '매우_불량한_순응도_(<40%)'
    END as adherence_category,
    COUNT(*) as patient_count,
    ROUND(AVG(mpr_percentage), 2) as avg_mpr,
    ROUND(AVG(total_prescriptions), 1) as avg_prescriptions,
    ROUND(AVG(total_days_supplied), 1) as avg_days_supplied,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage_of_patients,
    -- 임상적 해석
    CASE
        WHEN AVG(mpr_percentage) >= 80 THEN '임상적으로_적절한_순응도'
        WHEN AVG(mpr_percentage) >= 60 THEN '개선_필요한_순응도'
        ELSE '임상적_우려_수준'
    END as clinical_interpretation
FROM mpr_calculations
GROUP BY adherence_category
ORDER BY avg_mpr DESC;