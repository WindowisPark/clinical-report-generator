-- 특정 질환으로 병원을 방문한 환자들의 각 방문별 상세 처방 성분 내역 조회
-- 파라미터: disease_keyword = {{ disease_keyword }}

WITH `uc_visits` AS (
    SELECT DISTINCT
        `bt`.`user_id`,
        `bt`.`res_treat_start_date`,
        `bt`.`res_hospital_name`
    FROM `basic_treatment` AS `bt`
    WHERE `bt`.`res_disease_name` LIKE '%{{ disease_keyword }}%'
        AND `bt`.`deleted` = FALSE
),
`uc_rx` AS (
    SELECT
        u.`user_id`,
        u.`res_treat_start_date`,
        COALESCE(`pd`.`res_hospital_name`, u.`res_hospital_name`) AS `hospital_name`,
        `pd`.`res_ingredients`
    FROM `uc_visits` u
    JOIN `prescribed_drug` pd
        ON u.`user_id` = pd.`user_id`
        AND u.`res_treat_start_date` = pd.`res_treat_start_date`
    WHERE `pd`.`deleted` = FALSE
)
SELECT
    `user_id`,
    `res_treat_start_date`,
    `hospital_name`,
    array_join(collect_set(`res_ingredients`), ', ') AS `ingredients_list`
FROM `uc_rx`
GROUP BY `user_id`, `res_treat_start_date`, `hospital_name`
ORDER BY `user_id`, `res_treat_start_date`
LIMIT 10000;