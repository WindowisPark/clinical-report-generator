-- 파라미터: act_kw 에 행위명 키워드 입력 (예: MAST, 알레르겐, 알레르기)
WITH acts AS (  -- 키워드가 포함된 행위가 수행된 (user_id, 진료일) 집합
    SELECT DISTINCT
        dt.user_id,
        dt.res_treat_start_date
    FROM `detail_treatment` dt
    WHERE UPPER(dt.res_code_name) LIKE CONCAT('%', UPPER('{{ act_kw }}'), '%')
        AND dt.deleted = FALSE
),
act_hits AS (  -- 해당 날짜에 매칭된 행위명(코드명) 모음
    SELECT
        dt.user_id,
        dt.res_treat_start_date,
        COLLECT_SET(dt.res_code_name) AS matched_act_names
    FROM `detail_treatment` dt
    WHERE UPPER(dt.res_code_name) LIKE CONCAT('%', UPPER('{{ act_kw }}'), '%')
        AND dt.deleted = FALSE
    GROUP BY dt.user_id, dt.res_treat_start_date
),
diag AS (  -- 같은 날짜의 진단/코드/병원 모음
    SELECT
        bt.user_id,
        bt.res_treat_start_date,
        COLLECT_SET(bt.res_disease_name) AS disease_names,
        COLLECT_SET(bt.res_disease_code) AS disease_codes,
        COLLECT_SET(bt.res_hospital_name) AS hospital_names
    FROM `basic_treatment` bt
    WHERE bt.deleted = FALSE
    GROUP BY bt.user_id, bt.res_treat_start_date
)
SELECT
    a.user_id,
    a.res_treat_start_date,
    d.disease_names,
    d.disease_codes,
    d.hospital_names,
    h.matched_act_names  -- 요청: 행위명도 함께 출력
FROM acts a
INNER JOIN diag d
    ON a.user_id = d.user_id
   AND a.res_treat_start_date = d.res_treat_start_date
INNER JOIN act_hits h
    ON a.user_id = h.user_id
   AND a.res_treat_start_date = h.res_treat_start_date
ORDER BY a.res_treat_start_date DESC, a.user_id
LIMIT 1000;