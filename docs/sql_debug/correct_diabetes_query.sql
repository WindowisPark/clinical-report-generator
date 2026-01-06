-- 정확한 스키마 기반 당뇨병 환자 풀 분석 쿼리
-- notion_columns_improved.csv 기반으로 실제 컬럼 타입 반영

-- 중요한 발견사항:
-- res_treat_start_date: char(200) - 문자열 타입!
-- deleted: bit(1) - 0/1 값

WITH diabetes_patients AS (
    SELECT
        user_id,
        COUNT(*) as total_visits,
        MIN(res_treat_start_date) as first_visit,
        MAX(res_treat_start_date) as last_visit
    FROM basic_treatment
    WHERE (res_disease_name LIKE '%당뇨%'
        OR res_disease_name LIKE '%diabetes%'
        OR res_disease_name LIKE '%DM%'
        OR res_disease_name LIKE '%혈당%')
        AND deleted = 0  -- bit(1) 타입이므로 0 사용
        -- 날짜 조건 일단 제거 (char 타입이므로 형식 확인 필요)
    GROUP BY user_id
),
patient_analysis AS (
    SELECT
        COUNT(DISTINCT user_id) as total_diabetes_patients,
        COUNT(DISTINCT CASE WHEN total_visits >= 2 THEN user_id END) as active_patients,
        COUNT(DISTINCT CASE WHEN total_visits >= 5 THEN user_id END) as very_active_patients
    FROM diabetes_patients
)

SELECT
    '당뇨병 환자 풀 분석 (스키마 수정)' as analysis_type,
    total_diabetes_patients as `전체_당뇨병_환자`,
    active_patients as `활성_환자_2회이상`,
    very_active_patients as `매우활성_환자_5회이상`
FROM patient_analysis;

-- 추가 디버깅: 날짜 형식 확인용 쿼리
-- SELECT DISTINCT res_treat_start_date
-- FROM basic_treatment
-- WHERE res_disease_name LIKE '%당뇨%'
-- LIMIT 10;

/*
스키마 수정 사항:
1. deleted = false → deleted = 0 (bit(1) 타입)
2. 날짜 조건 일단 제거 (char(200) 타입 확인 필요)
3. 방문 횟수 기반 활성도만 측정

다음 단계:
1. 이 쿼리로 기본 환자 수 확인
2. res_treat_start_date 형식 확인 후 날짜 필터링 추가
3. 필요시 다른 테이블과 조인
*/