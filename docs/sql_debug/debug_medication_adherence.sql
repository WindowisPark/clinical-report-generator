-- MPR 복약순응도 디버깅 쿼리
-- 단계별로 데이터 존재 여부 확인

-- 1단계: 대상 환자 수 확인
SELECT '1. 대상 환자 수' as step, COUNT(DISTINCT bt.user_id) as count
FROM basic_treatment bt
WHERE bt.res_disease_name LIKE '%고혈압%'
    AND bt.res_treat_start_date >= '2022-01-01'
    AND bt.res_treat_start_date <= '2024-12-31'
    AND bt.deleted = false

UNION ALL

-- 2단계: 처방 데이터 존재 여부 확인
SELECT '2. 전체 처방 데이터' as step, COUNT(*) as count
FROM prescribed_drug pd
WHERE pd.deleted = false
    AND pd.res_total_dosing_days IS NOT NULL
    AND pd.res_total_dosing_days != ''

UNION ALL

-- 3단계: 성분명 데이터 확인
SELECT '3. 성분명 있는 처방' as step, COUNT(*) as count
FROM prescribed_drug pd
WHERE pd.deleted = false
    AND pd.res_ingredients IS NOT NULL
    AND pd.res_ingredients != ''

UNION ALL

-- 4단계: 숫자형 투약일수 확인
SELECT '4. 유효한 투약일수' as step, COUNT(*) as count
FROM prescribed_drug pd
WHERE pd.deleted = false
    AND pd.res_total_dosing_days REGEXP '^[0-9]+$'
    AND CAST(pd.res_total_dosing_days AS INT) > 0
    AND CAST(pd.res_total_dosing_days AS INT) <= 180

UNION ALL

-- 5단계: 고혈압 환자의 처방 데이터
SELECT '5. 고혈압 환자 처방' as step, COUNT(DISTINCT pd.user_id) as count
FROM prescribed_drug pd
JOIN (
    SELECT DISTINCT bt.user_id
    FROM basic_treatment bt
    WHERE bt.res_disease_name LIKE '%고혈압%'
        AND bt.res_treat_start_date >= '2022-01-01'
        AND bt.res_treat_start_date <= '2024-12-31'
        AND bt.deleted = false
) target_patients ON pd.user_id = target_patients.user_id
WHERE pd.deleted = false

UNION ALL

-- 6단계: 상위 성분명 확인 (샘플)
SELECT '6. 상위 성분명 예시' as step, 0 as count;

-- 상위 성분명 TOP 10
SELECT '성분명 샘플:' as step, pd.res_ingredients as count
FROM prescribed_drug pd
JOIN (
    SELECT DISTINCT bt.user_id
    FROM basic_treatment bt
    WHERE bt.res_disease_name LIKE '%고혈압%'
        AND bt.res_treat_start_date >= '2022-01-01'
        AND bt.res_treat_start_date <= '2024-12-31'
        AND bt.deleted = false
) target_patients ON pd.user_id = target_patients.user_id
WHERE pd.deleted = false
    AND pd.res_ingredients IS NOT NULL
    AND pd.res_ingredients != ''
GROUP BY pd.res_ingredients
ORDER BY COUNT(*) DESC
LIMIT 10;