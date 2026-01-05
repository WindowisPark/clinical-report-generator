-- 고도화된 지역 클러스터링 및 의료 밀도 분석
-- 파라미터: disease_name_keyword = {{ disease_name_keyword }}, start_date = {{ start_date }}, end_date = {{ end_date }}, min_patient_count = {{ min_patient_count }}, top_n = {{ top_n }}

-- A. 성능 최적화: 기간/질환으로 사전 필터링
WITH filtered_treatments AS (
    SELECT
        bt.user_id,
        bt.res_hospital_code,
        CAST(REGEXP_REPLACE(bt.res_total_amount, '[^0-9]', '') AS DECIMAL) as treatment_cost,
        bt.created_at
    FROM basic_treatment bt
    WHERE bt.res_disease_name LIKE '%{{ disease_name_keyword }}%' -- 파라미터 1
        AND bt.res_treat_start_date >= DATE '{{ start_date }}'   -- 파라미터 2 (통일: res_treat_start_date)
        AND bt.res_treat_start_date < DATE '{{ end_date }}'      -- 파라미터 3 (통일: res_treat_start_date)
        AND bt.deleted = false
        AND bt.res_total_amount IS NOT NULL
        AND CAST(REGEXP_REPLACE(bt.res_total_amount, '[^0-9]', '') AS DECIMAL) > 0
),
-- A. 데이터 정제: 지역명 표준화 및 NULL 처리
clean_geography AS (
    SELECT
        TRIM(NULLIF(h.sido_name, '')) as sido_name,
        TRIM(NULLIF(h.sigungu_name, '')) as sigungu_name,
        h.hospital_code
    FROM hospital h
    WHERE TRIM(NULLIF(h.sido_name, '')) IS NOT NULL
        AND TRIM(NULLIF(h.sigungu_name, '')) IS NOT NULL
),
-- 지역별 기초 통계
geographic_base AS (
    SELECT
        cg.sido_name,
        cg.sigungu_name,
        COUNT(DISTINCT ft.user_id) as patients,
        COUNT(DISTINCT cg.hospital_code) as hospitals,
        COUNT(*) as total_treatments,
        ROUND(COUNT(DISTINCT ft.user_id) * 1.0 / COUNT(DISTINCT cg.hospital_code), 2) as patient_per_hospital,
        -- D. 강건한 비용 통계
        ROUND(AVG(ft.treatment_cost), 0) as avg_cost,
        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ft.treatment_cost), 0) as median_cost,
        ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ft.treatment_cost), 0) as q1_cost,
        ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ft.treatment_cost), 0) as q3_cost
    FROM filtered_treatments ft
    JOIN clean_geography cg ON ft.res_hospital_code = cg.hospital_code
    GROUP BY cg.sido_name, cg.sigungu_name
    HAVING COUNT(DISTINCT ft.user_id) >= {{ min_patient_count | default(10) }}  -- 최소 환자수 필터
),
-- 윈저라이즈를 위한 전체 비용 분위수 계산
cost_bounds AS (
    SELECT
        PERCENTILE_CONT(0.01) WITHIN GROUP (ORDER BY treatment_cost) as cost_p01,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY treatment_cost) as cost_p99
    FROM filtered_treatments
),
-- 윈저라이즈된 지역별 평균 계산
winsorized_regional_costs AS (
    SELECT
        cg.sido_name,
        cg.sigungu_name,
        ROUND(AVG(CASE
            WHEN ft.treatment_cost BETWEEN cb.cost_p01 AND cb.cost_p99
            THEN ft.treatment_cost
        END), 0) as winsorized_avg_cost
    FROM filtered_treatments ft
    JOIN clean_geography cg ON ft.res_hospital_code = cg.hospital_code
    CROSS JOIN cost_bounds cb
    GROUP BY cg.sido_name, cg.sigungu_name
),
-- E. 분위수 기반 밀도 레벨 계산
density_quartiles AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY patient_per_hospital) as density_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY patient_per_hospital) as density_q3
    FROM geographic_base
),
regional_analysis AS (
    SELECT
        gb.*,
        wrc.winsorized_avg_cost,
        -- E. 적응형 밀도 분류 (분위수 기반)
        CASE
            WHEN gb.patient_per_hospital >= dq.density_q3 THEN '고밀도'
            WHEN gb.patient_per_hospital >= dq.density_q1 THEN '중밀도'
            ELSE '저밀도'
        END as density_level,
        -- IQR 범위
        (gb.q3_cost - gb.q1_cost) as iqr_range,
        -- 에피소드당 평균 비용 (환자당 총 비용)
        ROUND(gb.avg_cost * gb.total_treatments / gb.patients, 0) as avg_episode_cost
    FROM geographic_base gb
    CROSS JOIN density_quartiles dq
    LEFT JOIN winsorized_regional_costs wrc ON gb.sido_name = wrc.sido_name AND gb.sigungu_name = wrc.sigungu_name
)

SELECT
    '7. 고도화된 지역 밀도 분석' as analysis_type,
    sido_name,
    sigungu_name,
    patients as `환자수`,
    hospitals as `병원수`,
    patient_per_hospital as `병원당_환자수`,
    density_level as `밀도수준`,
    avg_cost as `평균_방문비용`,
    median_cost as `중앙값_방문비용`,
    winsorized_avg_cost as `윈저라이즈_평균비용`,
    iqr_range as `IQR_범위`,
    avg_episode_cost as `에피소드당_평균비용`
FROM regional_analysis
ORDER BY patients DESC
LIMIT {{ top_n | default(10) }};