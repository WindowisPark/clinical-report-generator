-- 개선된 Real-World Evidence (RWE) 분석
-- 파라미터: disease_code_prefix = {{ disease_code_prefix }}, start_date = {{ start_date }}, end_date = {{ end_date }}, min_pattern_size = {{ min_pattern_size }}

-- 1단계: 기간/질환 사전 필터링 (대폭 스캔 축소)
WITH filtered_treatments AS (
    SELECT
        bt.user_id,
        DATE(bt.created_at) as visit_date,  -- 날짜만 추출
        TRY_CAST(REGEXP_REPLACE(bt.res_total_amount, '[^0-9]', '') AS DECIMAL) as treatment_cost,
        u.birthday
    FROM basic_treatment bt
    JOIN user u ON bt.user_id = u.id
    WHERE bt.res_disease_name LIKE '%{{ disease_name_keyword }}%' -- 파라미터 1
        AND bt.created_at >= DATE '{{ start_date }}'             -- 파라미터 2
        AND bt.created_at < DATE '{{ end_date }}'                -- 파라미터 3
        AND bt.deleted = false
        AND u.birthday IS NOT NULL
        AND LENGTH(u.birthday) >= 4
        AND bt.res_total_amount IS NOT NULL
        AND bt.res_total_amount RLIKE '^[0-9]+$'  -- 정규식 최적화
        AND TRY_CAST(REGEXP_REPLACE(bt.res_total_amount, '[^0-9]', '') AS DECIMAL) > 0
),
-- 2단계: 환자별 집계 (윈도우 함수 제거, 한번에 모든 집계)
patient_visits AS (
    SELECT
        user_id,
        COUNT(DISTINCT visit_date) as total_visits,  -- 방문 날짜 기준
        MIN(visit_date) as first_visit,
        MAX(visit_date) as last_visit,
        DATEDIFF(MAX(visit_date), MIN(visit_date)) + 1 as treatment_duration_days,
        AVG(treatment_cost) as avg_cost_per_visit,  -- 방문당 평균 비용
        SUM(treatment_cost) / COUNT(DISTINCT visit_date) as avg_cost_per_day,  -- 방문일당 평균 비용
        -- 생년 정보도 한번에 가져오기 (중복 스캔 제거)
        FIRST(birthday) as birthday
    FROM filtered_treatments
    GROUP BY user_id
),
-- 3단계: 연령 계산 최적화 (중복 조인 제거)
patient_demographics AS (
    SELECT
        pv.user_id,
        pv.total_visits,
        pv.first_visit,
        pv.last_visit,
        pv.treatment_duration_days,
        pv.avg_cost_per_visit,
        pv.avg_cost_per_day,
        -- 연령 계산을 한번에 처리 (캐스팅 비용 절약)
        YEAR(pv.first_visit) -
        CASE
            WHEN LENGTH(pv.birthday) >= 8 THEN CAST(SUBSTRING(pv.birthday, 1, 4) AS INTEGER)
            WHEN LENGTH(pv.birthday) >= 6 THEN
                CASE
                    WHEN CAST(SUBSTRING(pv.birthday, 1, 2) AS INTEGER) <= 30 THEN 2000 + CAST(SUBSTRING(pv.birthday, 1, 2) AS INTEGER)
                    ELSE 1900 + CAST(SUBSTRING(pv.birthday, 1, 2) AS INTEGER)
                END
            ELSE NULL
        END as age_at_first_visit
    FROM patient_visits pv
),
-- 4단계: RWE 패턴 분류 (SARGable 조건 최적화)
rwe_patterns AS (
    SELECT
        user_id,
        total_visits,
        first_visit,
        last_visit,
        treatment_duration_days,
        avg_cost_per_visit,
        avg_cost_per_day,
        age_at_first_visit,
        -- 치료 패턴 분류 (성능을 위해 단순화)
        CASE
            WHEN treatment_duration_days >= 365 AND total_visits >= 4 THEN '장기_지속관리'
            WHEN treatment_duration_days >= 180 AND total_visits >= 3 THEN '중장기_추적'
            WHEN treatment_duration_days >= 90 AND total_visits >= 2 THEN '중기_치료'
            WHEN treatment_duration_days <= 30 AND total_visits = 1 THEN '단발_치료'
            WHEN treatment_duration_days <= 90 THEN '단기_치료'
            ELSE '불규칙_패턴'
        END as treatment_pattern,
        -- 참여도 분류 (인덱스 친화적 조건)
        CASE
            WHEN total_visits >= 6 THEN '고참여'
            WHEN total_visits >= 3 THEN '중참여'
            WHEN total_visits >= 2 THEN '저참여'
            ELSE '일회성'
        END as engagement_level,
        -- 비용 패턴 분류 (임계값 단순화)
        CASE
            WHEN avg_cost_per_visit >= 150000 THEN '고비용_패턴'
            WHEN avg_cost_per_visit >= 50000 THEN '중비용_패턴'
            ELSE '저비용_패턴'
        END as cost_pattern
    FROM patient_demographics
    WHERE age_at_first_visit IS NOT NULL
        AND age_at_first_visit >= 18  -- SARGable 조건
        AND age_at_first_visit <= 100
        AND total_visits > 0  -- 데이터 품질 보장
)

-- 5단계: 최종 집계 (DISTINCT 최소화, 서브쿼리 제거)
SELECT
    '8. 최적화된 RWE 치료 패턴' as analysis_type,
    treatment_pattern,
    engagement_level,
    cost_pattern,
    COUNT(*) as patient_count,
    ROUND(AVG(age_at_first_visit), 1) as avg_age_at_start,
    ROUND(AVG(total_visits), 1) as avg_visit_days,
    ROUND(AVG(treatment_duration_days), 1) as avg_duration_days,
    ROUND(AVG(avg_cost_per_visit), 0) as avg_cost_per_visit,
    ROUND(AVG(avg_cost_per_day), 0) as avg_cost_per_day,
    -- 서브쿼리 제거로 성능 향상
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pattern_percentage
FROM rwe_patterns
GROUP BY treatment_pattern, engagement_level, cost_pattern
HAVING COUNT(*) >= {{ min_pattern_size }}  -- 최소 패턴 크기 이상만 표시
ORDER BY patient_count DESC;