WITH recruitment_feasibility AS (
    SELECT
        COUNT(DISTINCT bt.user_id) as total_pool,
        COUNT(DISTINCT CASE WHEN (YEAR(CURRENT_DATE()) -
            CASE
                WHEN LENGTH(u.birthday) >= 8 THEN CAST(SUBSTRING(u.birthday, 1, 4) AS INTEGER)
                WHEN LENGTH(u.birthday) >= 6 THEN (CASE WHEN CAST(SUBSTRING(u.birthday, 1, 2) AS INTEGER) <= 30 THEN 2000 ELSE 1900 END) + CAST(SUBSTRING(u.birthday, 1, 2) AS INTEGER)
                ELSE NULL
            END) BETWEEN {{ min_age }} AND {{ max_age }} THEN bt.user_id END) as adult_pool,
        COUNT(DISTINCT CASE WHEN visit_counts.total_visits >= {{ min_visits }} THEN bt.user_id END) as engaged_pool,
        COUNT(DISTINCT CASE WHEN
            (YEAR(CURRENT_DATE()) -
            CASE
                WHEN LENGTH(u.birthday) >= 8 THEN CAST(SUBSTRING(u.birthday, 1, 4) AS INTEGER)
                WHEN LENGTH(u.birthday) >= 6 THEN (CASE WHEN CAST(SUBSTRING(u.birthday, 1, 2) AS INTEGER) <= 30 THEN 2000 ELSE 1900 END) + CAST(SUBSTRING(u.birthday, 1, 2) AS INTEGER)
                ELSE NULL
            END) BETWEEN {{ min_age }} AND {{ max_age }} AND visit_counts.total_visits >= {{ min_visits }} THEN bt.user_id END) as qualified_pool,
        {{ target_enrollment }} as target_enrollment
    FROM basic_treatment bt
    JOIN user u ON bt.user_id = u.id
    JOIN (
        SELECT user_id, COUNT(*) as total_visits
        FROM basic_treatment
        WHERE res_disease_name LIKE '%{{ disease_name_keyword }}%' -- 파라미터 1
            AND res_treat_start_date >= '{{ start_date }}'    -- 파라미터 2 (통일: res_treat_start_date 사용)
            AND deleted = false
        GROUP BY user_id
    ) visit_counts ON bt.user_id = visit_counts.user_id
    WHERE bt.res_disease_name LIKE '%{{ disease_name_keyword }}%' -- 파라미터 1
        AND bt.res_treat_start_date >= '{{ start_date }}'     -- 파라미터 2 (통일: res_treat_start_date 사용)
        AND bt.res_treat_start_date <= '{{ end_date }}'       -- 파라미터 3 (통일: res_treat_start_date 사용)
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
    ROUND(qualified_pool * {{ expected_participation_rate }}, 0) as `예상_실제_모집가능수`, -- 파라미터 8
    ROUND(qualified_pool * {{ expected_screening_rate }}, 0) as `예상_스크리닝_전체수`  -- 파라미터 9
FROM recruitment_feasibility;