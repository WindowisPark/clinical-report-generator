-- Generated from: analyze_recruitment_feasibility.yaml
-- Parameters used: {'disease_name_keyword': '당뇨병', 'start_date': '2022-01-01', 'end_date': '2024-12-31', 'min_age': 19, 'max_age': 120, 'min_visits': 1, 'target_enrollment': 10, 'expected_participation_rate': 0.1, 'expected_screening_rate': 0.5, 'snapshot_dt': '2025-09-01'}

WITH recruitment_feasibility AS (
    SELECT
        COUNT(DISTINCT bt.user_id) as total_pool,
        COUNT(DISTINCT CASE WHEN (YEAR(CURRENT_DATE()) -
            CASE
                WHEN LENGTH(u.birthday) >= 8 THEN CAST(SUBSTRING(u.birthday, 1, 4) AS INT)
                WHEN LENGTH(u.birthday) >= 6 THEN (CASE WHEN CAST(SUBSTRING(u.birthday, 1, 2) AS INT) <= 30 THEN 2000 ELSE 1900 END) + CAST(SUBSTRING(u.birthday, 1, 2) AS INT)
                ELSE NULL
            END) BETWEEN 19 AND 120 THEN bt.user_id END) as adult_pool,
        COUNT(DISTINCT CASE WHEN visit_counts.total_visits >= 1 THEN bt.user_id END) as engaged_pool,
        COUNT(DISTINCT CASE WHEN
            (YEAR(CURRENT_DATE()) -
            CASE
                WHEN LENGTH(u.birthday) >= 8 THEN CAST(SUBSTRING(u.birthday, 1, 4) AS INT)
                WHEN LENGTH(u.birthday) >= 6 THEN (CASE WHEN CAST(SUBSTRING(u.birthday, 1, 2) AS INT) <= 30 THEN 2000 ELSE 1900 END) + CAST(SUBSTRING(u.birthday, 1, 2) AS INT)
                ELSE NULL
            END) BETWEEN 19 AND 120 AND visit_counts.total_visits >= 1 THEN bt.user_id END) as qualified_pool,
        10 as target_enrollment
    FROM basic_treatment bt
    JOIN user u ON bt.user_id = u.id
    JOIN (
        SELECT user_id, COUNT(*) as total_visits
        FROM basic_treatment
        WHERE res_disease_name LIKE '%당뇨병%' -- 파라미터 1
            AND created_at >= '2022-01-01'               -- 파라미터 2
            AND deleted = false
        GROUP BY user_id
    ) visit_counts ON bt.user_id = visit_counts.user_id
    WHERE bt.res_disease_name LIKE '%당뇨병%' -- 파라미터 1
        AND bt.created_at >= '2022-01-01'               -- 파라미터 2
        AND bt.created_at <= '2024-12-31'                 -- 파라미터 3
        AND bt.deleted = false
        AND u.birthday IS NOT NULL
        AND LENGTH(u.birthday) >= 4
)

SELECT
    '5. 모집 타당성' as analysis_type,
    total_pool as `전체_환자_풀`,
    adult_pool as `성인_환자_풀`,
    engaged_pool as `참여_가능_풀`,
    qualified_pool as `자격_만족_풀`,
    target_enrollment as `목표_모집수`,
    ROUND(qualified_pool * 1.0 / target_enrollment, 2) as `풀_대비_목표_비율`,
    CASE
        WHEN qualified_pool >= target_enrollment * 10 THEN '매우 양호 (10:1 이상)'
        WHEN qualified_pool >= target_enrollment * 5 THEN '양호 (5:1 이상)'
        WHEN qualified_pool >= target_enrollment * 3 THEN '보통 (3:1 이상)'
        WHEN qualified_pool >= target_enrollment * 1.5 THEN '도전적 (1.5:1 이상)'
        ELSE '매우 도전적 (1.5:1 미만)'
    END as `모집_난이도`,
    ROUND(qualified_pool * 0.1, 0) as `예상_실제_모집가능수`, -- 파라미터 8
    ROUND(qualified_pool * 0.5, 0) as `예상_스크리닝_전체수`  -- 파라미터 9
FROM recruitment_feasibility;