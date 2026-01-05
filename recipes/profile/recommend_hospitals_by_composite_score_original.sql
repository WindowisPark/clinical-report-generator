-- 복합 점수 기반 병원 추천 시스템 (정교화된 표준화 방식)
-- 파라미터: disease_code_prefix = {{ disease_code_prefix }}, start_date = {{ start_date }}, end_date = {{ end_date }}, effectiveness_weight = {{ effectiveness_weight }}, satisfaction_weight = {{ satisfaction_weight }}, accessibility_weight = {{ accessibility_weight }}, min_patient_count = {{ min_patient_count }}

-- 1단계: 기본 병원 데이터 수집
WITH hospital_base_data AS (
    SELECT
        bt.res_hospital_code,
        h.medical_facility_name,
        h.medical_facility_type_code,
        h.location_address,
        COUNT(DISTINCT bt.user_id) as total_patients,
        COUNT(DISTINCT bt.id) as total_visits,
        COUNT(DISTINCT DATE(bt.created_at)) as active_days
    FROM basic_treatment bt
    JOIN hospital h ON bt.res_hospital_code = h.medical_facility_code
    WHERE bt.res_disease_name LIKE '%{{ disease_name_keyword }}%'
        AND bt.created_at >= '{{ start_date }}'
        AND bt.created_at <= '{{ end_date }}'
        AND bt.deleted = false
    GROUP BY bt.res_hospital_code, h.medical_facility_name, h.medical_facility_type_code, h.location_address
    HAVING COUNT(DISTINCT bt.user_id) >= {{ min_patient_count }}
),

-- 2단계: 처방 변경 유형 분류 (Proxy 지표 개선)
prescription_change_analysis AS (
    SELECT
        bt.res_hospital_code,
        pd.user_id,
        pd.res_ingredients,
        pd.res_drug_name,
        ROW_NUMBER() OVER (PARTITION BY bt.res_hospital_code, pd.user_id ORDER BY pd.created_at) as prescription_order,
        LAG(pd.res_ingredients) OVER (PARTITION BY bt.res_hospital_code, pd.user_id ORDER BY pd.created_at) as prev_ingredients,
        LAG(pd.res_drug_name) OVER (PARTITION BY bt.res_hospital_code, pd.user_id ORDER BY pd.created_at) as prev_drug_name,
        -- 변경 유형 분류
        CASE
            WHEN LAG(pd.res_ingredients) OVER (PARTITION BY bt.res_hospital_code, pd.user_id ORDER BY pd.created_at) IS NULL THEN 'Initial_Prescription'
            WHEN LAG(pd.res_ingredients) OVER (PARTITION BY bt.res_hospital_code, pd.user_id ORDER BY pd.created_at) != pd.res_ingredients
                 AND LAG(pd.res_drug_name) OVER (PARTITION BY bt.res_hospital_code, pd.user_id ORDER BY pd.created_at) != pd.res_drug_name THEN 'Major_Change'
            WHEN LAG(pd.res_drug_name) OVER (PARTITION BY bt.res_hospital_code, pd.user_id ORDER BY pd.created_at) != pd.res_drug_name THEN 'Within_Class_Change'
            ELSE 'Dose_Adjustment'
        END as change_type
    FROM basic_treatment bt
    JOIN prescribed_drug pd ON bt.user_id = pd.user_id
    WHERE bt.res_disease_name LIKE '%{{ disease_name_keyword }}%'
        AND bt.created_at >= '{{ start_date }}'
        AND bt.created_at <= '{{ end_date }}'
        AND bt.deleted = false
        AND pd.deleted = false
),

-- 3단계: 환자 재방문 패턴 분석
patient_retention_analysis AS (
    SELECT
        bt.res_hospital_code,
        bt.user_id,
        MIN(DATE(bt.created_at)) as first_visit,
        MAX(DATE(bt.created_at)) as last_visit,
        COUNT(DISTINCT DATE(bt.created_at)) as visit_count,
        DATEDIFF(MAX(DATE(bt.created_at)), MIN(DATE(bt.created_at))) as treatment_duration_days,
        -- 최적 방문 간격 점수 (7-30일 간격이 이상적)
        CASE
            WHEN COUNT(DISTINCT DATE(bt.created_at)) = 1 THEN 0
            ELSE ROUND(DATEDIFF(MAX(DATE(bt.created_at)), MIN(DATE(bt.created_at))) / (COUNT(DISTINCT DATE(bt.created_at)) - 1), 1)
        END as avg_visit_interval
    FROM basic_treatment bt
    WHERE bt.res_disease_name LIKE '%{{ disease_name_keyword }}%'
        AND bt.created_at >= '{{ start_date }}'
        AND bt.created_at <= '{{ end_date }}'
        AND bt.deleted = false
    GROUP BY bt.res_hospital_code, bt.user_id
),

-- 4단계: 병원별 성과 지표 계산
hospital_performance_metrics AS (
    SELECT
        hbd.res_hospital_code,
        hbd.medical_facility_name,
        hbd.medical_facility_type_code,
        hbd.location_address,
        hbd.total_patients,
        hbd.total_visits,
        hbd.active_days,

        -- 치료 효과성 지표
        ROUND(AVG(pra.treatment_duration_days), 1) as avg_treatment_duration,
        ROUND(COUNT(CASE WHEN pra.visit_count >= 3 THEN 1 END) * 100.0 / COUNT(*), 2) as patient_retention_rate,
        ROUND(SUM(CASE WHEN pca.change_type = 'Major_Change' THEN 1 ELSE 0 END) * 100.0 /
              NULLIF(SUM(CASE WHEN pca.change_type != 'Initial_Prescription' THEN 1 ELSE 0 END), 0), 2) as major_change_rate,

        -- 환자 만족도 proxy 지표
        ROUND(AVG(pra.visit_count), 1) as avg_visits_per_patient,
        ROUND(AVG(CASE WHEN pra.avg_visit_interval BETWEEN 7 AND 30 THEN 1 ELSE 0 END) * 100.0, 2) as optimal_interval_rate,

        -- 접근성 지표
        ROUND(hbd.total_visits * 1.0 / hbd.active_days, 2) as daily_capacity_utilization

    FROM hospital_base_data hbd
    LEFT JOIN patient_retention_analysis pra ON hbd.res_hospital_code = pra.res_hospital_code
    LEFT JOIN prescription_change_analysis pca ON hbd.res_hospital_code = pca.res_hospital_code
    GROUP BY hbd.res_hospital_code, hbd.medical_facility_name, hbd.medical_facility_type_code,
             hbd.location_address, hbd.total_patients, hbd.total_visits, hbd.active_days
),

-- 5단계: 다중 표준화 방법 적용
standardization_calculations AS (
    SELECT
        *,
        -- Min-Max 표준화 (0-1 범위)
        (patient_retention_rate - MIN(patient_retention_rate) OVER()) /
        NULLIF(MAX(patient_retention_rate) OVER() - MIN(patient_retention_rate) OVER(), 0) as retention_minmax,

        (100 - major_change_rate - MIN(100 - major_change_rate) OVER()) /
        NULLIF(MAX(100 - major_change_rate) OVER() - MIN(100 - major_change_rate) OVER(), 0) as effectiveness_minmax,

        (optimal_interval_rate - MIN(optimal_interval_rate) OVER()) /
        NULLIF(MAX(optimal_interval_rate) OVER() - MIN(optimal_interval_rate) OVER(), 0) as satisfaction_minmax,

        (daily_capacity_utilization - MIN(daily_capacity_utilization) OVER()) /
        NULLIF(MAX(daily_capacity_utilization) OVER() - MIN(daily_capacity_utilization) OVER(), 0) as accessibility_minmax,

        -- Z-Score 표준화 (평균 0, 표준편차 1)
        (patient_retention_rate - AVG(patient_retention_rate) OVER()) /
        NULLIF(STDDEV(patient_retention_rate) OVER(), 0) as retention_zscore,

        ((100 - major_change_rate) - AVG(100 - major_change_rate) OVER()) /
        NULLIF(STDDEV(100 - major_change_rate) OVER(), 0) as effectiveness_zscore,

        (optimal_interval_rate - AVG(optimal_interval_rate) OVER()) /
        NULLIF(STDDEV(optimal_interval_rate) OVER(), 0) as satisfaction_zscore,

        (daily_capacity_utilization - AVG(daily_capacity_utilization) OVER()) /
        NULLIF(STDDEV(daily_capacity_utilization) OVER(), 0) as accessibility_zscore,

        -- Percentile 순위
        PERCENT_RANK() OVER (ORDER BY patient_retention_rate) as retention_percentile,
        PERCENT_RANK() OVER (ORDER BY 100 - major_change_rate) as effectiveness_percentile,
        PERCENT_RANK() OVER (ORDER BY optimal_interval_rate) as satisfaction_percentile,
        PERCENT_RANK() OVER (ORDER BY daily_capacity_utilization) as accessibility_percentile

    FROM hospital_performance_metrics
),

-- 6단계: 복합 점수 계산 (여러 표준화 방법의 앙상블)
final_composite_scores AS (
    SELECT
        res_hospital_code,
        medical_facility_name,
        medical_facility_type_code,
        location_address,
        total_patients,
        patient_retention_rate,
        major_change_rate,
        optimal_interval_rate,
        daily_capacity_utilization,

        -- 개별 표준화 점수 (0-100 스케일)
        ROUND(COALESCE(retention_minmax, 0) * 100, 1) as retention_score_minmax,
        ROUND(COALESCE(effectiveness_minmax, 0) * 100, 1) as effectiveness_score_minmax,
        ROUND(COALESCE(satisfaction_minmax, 0) * 100, 1) as satisfaction_score_minmax,
        ROUND(COALESCE(accessibility_minmax, 0) * 100, 1) as accessibility_score_minmax,

        -- Z-Score 기반 점수 (50을 중심으로 ±3σ 범위를 0-100으로 매핑)
        ROUND(GREATEST(0, LEAST(100, 50 + COALESCE(retention_zscore, 0) * 16.67)), 1) as retention_score_zscore,
        ROUND(GREATEST(0, LEAST(100, 50 + COALESCE(effectiveness_zscore, 0) * 16.67)), 1) as effectiveness_score_zscore,
        ROUND(GREATEST(0, LEAST(100, 50 + COALESCE(satisfaction_zscore, 0) * 16.67)), 1) as satisfaction_score_zscore,
        ROUND(GREATEST(0, LEAST(100, 50 + COALESCE(accessibility_zscore, 0) * 16.67)), 1) as accessibility_score_zscore,

        -- Percentile 점수
        ROUND(COALESCE(retention_percentile, 0) * 100, 1) as retention_score_percentile,
        ROUND(COALESCE(effectiveness_percentile, 0) * 100, 1) as effectiveness_score_percentile,
        ROUND(COALESCE(satisfaction_percentile, 0) * 100, 1) as satisfaction_score_percentile,
        ROUND(COALESCE(accessibility_percentile, 0) * 100, 1) as accessibility_score_percentile,

        -- 앙상블 복합 점수 (3가지 방법의 평균)
        ROUND(
            ((COALESCE(retention_minmax, 0) +
              GREATEST(0, LEAST(1, 0.5 + COALESCE(retention_zscore, 0) / 6)) +
              COALESCE(retention_percentile, 0)) / 3) * {{ effectiveness_weight }} * 100 +
            ((COALESCE(effectiveness_minmax, 0) +
              GREATEST(0, LEAST(1, 0.5 + COALESCE(effectiveness_zscore, 0) / 6)) +
              COALESCE(effectiveness_percentile, 0)) / 3) * {{ effectiveness_weight }} * 100 +
            ((COALESCE(satisfaction_minmax, 0) +
              GREATEST(0, LEAST(1, 0.5 + COALESCE(satisfaction_zscore, 0) / 6)) +
              COALESCE(satisfaction_percentile, 0)) / 3) * {{ satisfaction_weight }} * 100 +
            ((COALESCE(accessibility_minmax, 0) +
              GREATEST(0, LEAST(1, 0.5 + COALESCE(accessibility_zscore, 0) / 6)) +
              COALESCE(accessibility_percentile, 0)) / 3) * {{ accessibility_weight }} * 100
        , 1) as ensemble_composite_score

    FROM standardization_calculations
)

-- 최종 결과: 복합 점수 기반 병원 추천 순위
SELECT
    '복합점수 병원 추천' as analysis_type,
    ROW_NUMBER() OVER (ORDER BY ensemble_composite_score DESC) as recommendation_rank,
    res_hospital_code,
    medical_facility_name,
    medical_facility_type_code,
    location_address,
    total_patients,
    ensemble_composite_score,

    -- 세부 성과 지표
    patient_retention_rate,
    major_change_rate,
    optimal_interval_rate,
    daily_capacity_utilization,

    -- 표준화 방법별 점수 비교
    retention_score_minmax,
    retention_score_zscore,
    retention_score_percentile,
    effectiveness_score_minmax,
    effectiveness_score_zscore,
    effectiveness_score_percentile,
    satisfaction_score_minmax,
    satisfaction_score_zscore,
    satisfaction_score_percentile,
    accessibility_score_minmax,
    accessibility_score_zscore,
    accessibility_score_percentile,

    -- 추천 등급
    CASE
        WHEN ensemble_composite_score >= 80 THEN 'A등급_강력추천'
        WHEN ensemble_composite_score >= 70 THEN 'B등급_추천'
        WHEN ensemble_composite_score >= 60 THEN 'C등급_보통'
        WHEN ensemble_composite_score >= 50 THEN 'D등급_신중검토'
        ELSE 'E등급_추천안함'
    END as recommendation_grade,

    -- 가중치 정보
    CONCAT('효과성:', ROUND({{ effectiveness_weight }} * 100, 0), '% / ',
           '만족도:', ROUND({{ satisfaction_weight }} * 100, 0), '% / ',
           '접근성:', ROUND({{ accessibility_weight }} * 100, 0), '%') as weight_distribution

FROM final_composite_scores
ORDER BY ensemble_composite_score DESC
LIMIT 20;