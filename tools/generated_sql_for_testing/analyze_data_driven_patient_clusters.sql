-- Generated from: analyze_data_driven_patient_clusters.yaml
-- Parameters used: {'disease_name_keyword': '당뇨병', 'start_date': '2022-01-01', 'end_date': '2024-12-31', 'num_clusters': 4, 'snapshot_dt': '2025-09-01'}

-- 환자 클러스터링 분석 (연령×방문×비용 기준)
-- 파라미터: disease_code_prefix = , start_date = 2022-01-01, end_date = 2024-12-31

WITH patient_base AS (
    SELECT
        bt.user_id,
        YEAR(CURRENT_DATE()) -
        CASE
            WHEN LENGTH(u.birthday) >= 8 THEN CAST(SUBSTRING(u.birthday, 1, 4) AS INT)
            WHEN LENGTH(u.birthday) >= 6 THEN
                CASE
                    WHEN CAST(SUBSTRING(u.birthday, 1, 2) AS INT) <= 30 THEN 2000 + CAST(SUBSTRING(u.birthday, 1, 2) AS INT)
                    ELSE 1900 + CAST(SUBSTRING(u.birthday, 1, 2) AS INT)
                END
            ELSE NULL
        END as age,
        COUNT(*) as total_visits,
        AVG(CAST(REGEXP_REPLACE(bt.res_total_amount, '[^0-9]', '') AS DECIMAL)) as avg_cost,
        DATEDIFF(MAX(bt.created_at), MIN(bt.created_at)) + 1 as treatment_duration_days
    FROM basic_treatment bt
    JOIN user u ON bt.user_id = u.id
    WHERE bt.res_disease_name LIKE '%당뇨병%' -- 파라미터 1
        AND bt.created_at >= '2022-01-01'               -- 파라미터 2
        AND bt.created_at <= '2024-12-31'                 -- 파라미터 3
        AND bt.deleted = false
        AND u.birthday IS NOT NULL
        AND LENGTH(u.birthday) >= 4
        AND bt.res_total_amount IS NOT NULL
    GROUP BY
        bt.user_id,
        u.birthday,
        YEAR(CURRENT_DATE()) -
        CASE
            WHEN LENGTH(u.birthday) >= 8 THEN CAST(SUBSTRING(u.birthday, 1, 4) AS INT)
            WHEN LENGTH(u.birthday) >= 6 THEN
                CASE
                    WHEN CAST(SUBSTRING(u.birthday, 1, 2) AS INT) <= 30 THEN 2000 + CAST(SUBSTRING(u.birthday, 1, 2) AS INT)
                    ELSE 1900 + CAST(SUBSTRING(u.birthday, 1, 2) AS INT)
                END
            ELSE NULL
        END
),
quartiles AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY age) as age_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY age) as age_q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_visits) as visits_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_visits) as visits_q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_cost) as cost_q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_cost) as cost_q3,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY treatment_duration_days) as duration_median
    FROM patient_base
),
patient_segments AS (
    SELECT
        pb.*,
        CASE
            WHEN pb.age < q.age_q1 THEN '청년층'
            WHEN pb.age <= q.age_q3 THEN '중년층'
            ELSE '장년층'
        END as age_segment,
        CASE
            WHEN pb.total_visits < q.visits_q1 THEN '저방문'
            WHEN pb.total_visits <= q.visits_q3 THEN '중방문'
            ELSE '고방문'
        END as visit_segment,
        CASE
            WHEN pb.avg_cost < q.cost_q1 THEN '저비용'
            WHEN pb.avg_cost <= q.cost_q3 THEN '중비용'
            ELSE '고비용'
        END as cost_segment,
        CASE
            WHEN pb.treatment_duration_days <= q.duration_median THEN '단기치료'
            ELSE '장기치료'
        END as duration_segment
    FROM patient_base pb
    CROSS JOIN quartiles q
),
clustered_patients AS (
    SELECT
        *,
        CONCAT(age_segment, '_', visit_segment, '_', cost_segment) as primary_cluster,
        CONCAT(age_segment, '_', visit_segment, '_', cost_segment, '_', duration_segment) as detailed_cluster
    FROM patient_segments
)

SELECT
    '6. 환자 클러스터 (연령×방문×비용 기준)' as analysis_type,
    primary_cluster as cluster_name,
    COUNT(*) as cluster_size,
    ROUND(AVG(age), 1) as avg_age,
    ROUND(AVG(total_visits), 1) as avg_visits,
    ROUND(AVG(avg_cost), 0) as avg_cost_per_visit,
    ROUND(AVG(treatment_duration_days), 1) as avg_duration_days,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM clustered_patients), 1) as percentage
FROM clustered_patients
GROUP BY primary_cluster
ORDER BY cluster_size DESC;