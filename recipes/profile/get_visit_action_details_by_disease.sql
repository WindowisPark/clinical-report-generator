-- 특정 질환으로 병원을 방문한 환자들의 각 방문별 상세 처치 내역 조회
-- 파라미터: disease_keyword = {{ disease_keyword }}

WITH amd_visits AS (
    SELECT DISTINCT
        bt.`user_id`,
        bt.`res_treat_start_date`,
        bt.`res_hospital_name`
    FROM `basic_treatment` bt
    WHERE bt.`res_disease_name` LIKE '%{{ disease_keyword }}%'
        AND bt.`deleted` = FALSE
),
amd_actions AS (
    SELECT
        a.`user_id`,
        a.`res_treat_start_date`,
        a.`res_hospital_name`,
        dt.`res_code_name`
    FROM amd_visits a
    JOIN `detail_treatment` dt
        ON a.`user_id` = dt.`user_id`
        AND a.`res_treat_start_date` = dt.`res_treat_start_date`
)
SELECT
    `user_id`,
    `res_treat_start_date`,
    `res_hospital_name`,
    array_join(collect_set(`res_code_name`), ', ') AS action_list
FROM amd_actions
GROUP BY `user_id`, `res_treat_start_date`, `res_hospital_name`
ORDER BY `user_id`, `res_treat_start_date`
LIMIT 10000;