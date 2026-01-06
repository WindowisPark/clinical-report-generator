-- 특정 질환 키워드를 가진 환자들의 병원별 방문 현황 분석
-- 파라미터: disease_keyword = {{ disease_keyword }}

SELECT
    `res_hospital_name` AS `병원명`,
    COUNT(DISTINCT `user_id`) AS `유니크_환자수`,
    COUNT(*) AS `총_방문횟수`
FROM `basic_treatment`
WHERE `res_disease_name` LIKE '%{{ disease_keyword }}%'
    AND `res_hospital_name` IS NOT NULL
    AND LOWER(`res_hospital_name`) NOT LIKE '%약국%' -- 약국 제외
    AND `deleted` = FALSE
GROUP BY `res_hospital_name`
ORDER BY `총_방문횟수` DESC
LIMIT 10000;