-- 특정 질환(포함 기준) 환자 중 복잡한 제외 기준에 해당하지 않는 환자들의 방문 기록 스크리닝
-- 파라미터: inclusion_disease_keyword = {{ inclusion_disease_keyword }}, exclusion_disease_keywords = {{ exclusion_disease_keywords }}, exclusion_drug_keywords = {{ exclusion_drug_keywords }}

WITH inclusion_patients AS (
    -- 포함 조건: 파라미터로 받은 질환
    SELECT DISTINCT bt.user_id, bt.res_treat_start_date, bt.res_hospital_code
    FROM basic_treatment bt
    WHERE bt.deleted = FALSE
      AND bt.res_disease_name LIKE CONCAT('%', '{{ inclusion_disease_keyword }}', '%')
),

exclusion_patients AS (
    -- 제외 조건: 파라미터로 받은 질환들
    SELECT DISTINCT bt.user_id
    FROM basic_treatment bt
    WHERE bt.deleted = FALSE
      AND (
        {% for keyword in exclusion_disease_keywords.split(',') %}
        bt.res_disease_name LIKE '%{{ keyword.strip() }}%'
        {% if not loop.last %} OR {% endif %}
        {% endfor %}
      )

    UNION

    -- 제외 조건: 파라미터로 받은 약물들
    SELECT DISTINCT pd.user_id
    FROM prescribed_drug pd
    WHERE (
        {% for keyword in exclusion_drug_keywords.split(',') %}
        pd.res_drug_name LIKE '%{{ keyword.strip() }}%'
        {% if not loop.last %} OR {% endif %}
        {% endfor %}
    )
),

drug_info AS (
    -- 약물 정보 (브랜드명, 성분명 같이 조회)
    SELECT
        pd.user_id,
        pd.res_treat_start_date,
        COLLECT_SET(pd.res_drug_name) AS drug_names,
        COLLECT_SET(pd.res_ingredients) AS ingredients
    FROM prescribed_drug pd
    WHERE pd.deleted = FALSE
    GROUP BY pd.user_id, pd.res_treat_start_date
),

hospital_info AS (
    -- 병원 등급 및 위치
    SELECT
        h.hospital_code,
        h.full_address,
        h.sido_name,
        h.sigungu_name,
        CASE
            WHEN h.medical_facility_type_code IN ('01','1') THEN '3차'
            WHEN h.medical_facility_type_code IN ('11','21','28','29','41','92') THEN '2차'
            ELSE '1차'
        END AS hospital_level
    FROM hospital h
)

SELECT
    ip.user_id,
    bt.res_treat_start_date AS treat_date,
    hi.hospital_level,
    hi.full_address,
    hi.sido_name,
    hi.sigungu_name,
    di.drug_names,
    di.ingredients
FROM inclusion_patients bt
LEFT JOIN exclusion_patients ep
    ON bt.user_id = ep.user_id
LEFT JOIN drug_info di
    ON bt.user_id = di.user_id
   AND bt.res_treat_start_date = di.res_treat_start_date
LEFT JOIN hospital_info hi
    ON bt.res_hospital_code = hi.hospital_code
LEFT JOIN insured_person ip
    ON bt.user_id = ip.user_id
WHERE ep.user_id IS NULL   -- 제외 조건에 해당하지 않는 환자만
ORDER BY bt.res_treat_start_date DESC;