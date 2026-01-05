-- Generated from: screen_visits_by_inclusion_exclusion_list.yaml
-- Parameters used: {'inclusion_disease_keyword': '당뇨병', 'exclusion_disease_keywords': '간염,HIV,AIDS,면역결핍,암,종양,백혈구감소,혈소판감소,호중구감소,빈혈,간경변,간부전,신부전,신장질환,심근경색,심부전,부정맥,COPD,만성폐쇄성폐질환,간질성폐질환,폐섬유화', 'exclusion_drug_keywords': '리툭시맙,에쿨리주맙,라불리주맙,efgartigimod,FcRn,ibrutinib,acalabrutinib,와파린,NOAC,아픽사반,리바록사반', 'snapshot_dt': '2025-09-01'}

-- 특정 질환(포함 기준) 환자 중 복잡한 제외 기준에 해당하지 않는 환자들의 방문 기록 스크리닝
-- 파라미터: inclusion_disease_keyword = 당뇨병, exclusion_disease_keywords = 간염,HIV,AIDS,면역결핍,암,종양,백혈구감소,혈소판감소,호중구감소,빈혈,간경변,간부전,신부전,신장질환,심근경색,심부전,부정맥,COPD,만성폐쇄성폐질환,간질성폐질환,폐섬유화, exclusion_drug_keywords = 리툭시맙,에쿨리주맙,라불리주맙,efgartigimod,FcRn,ibrutinib,acalabrutinib,와파린,NOAC,아픽사반,리바록사반

WITH inclusion_patients AS (
    -- 포함 조건: 파라미터로 받은 질환
    SELECT DISTINCT bt.user_id, bt.res_treat_start_date, bt.res_hospital_code
    FROM basic_treatment bt
    WHERE bt.deleted = FALSE
      AND bt.res_disease_name LIKE CONCAT('%', '당뇨병', '%')
),

exclusion_patients AS (
    -- 제외 조건: 파라미터로 받은 질환들
    SELECT DISTINCT bt.user_id
    FROM basic_treatment bt
    WHERE bt.deleted = FALSE
      AND (
        
        bt.res_disease_name LIKE '%간염%'
         OR 
        
        bt.res_disease_name LIKE '%HIV%'
         OR 
        
        bt.res_disease_name LIKE '%AIDS%'
         OR 
        
        bt.res_disease_name LIKE '%면역결핍%'
         OR 
        
        bt.res_disease_name LIKE '%암%'
         OR 
        
        bt.res_disease_name LIKE '%종양%'
         OR 
        
        bt.res_disease_name LIKE '%백혈구감소%'
         OR 
        
        bt.res_disease_name LIKE '%혈소판감소%'
         OR 
        
        bt.res_disease_name LIKE '%호중구감소%'
         OR 
        
        bt.res_disease_name LIKE '%빈혈%'
         OR 
        
        bt.res_disease_name LIKE '%간경변%'
         OR 
        
        bt.res_disease_name LIKE '%간부전%'
         OR 
        
        bt.res_disease_name LIKE '%신부전%'
         OR 
        
        bt.res_disease_name LIKE '%신장질환%'
         OR 
        
        bt.res_disease_name LIKE '%심근경색%'
         OR 
        
        bt.res_disease_name LIKE '%심부전%'
         OR 
        
        bt.res_disease_name LIKE '%부정맥%'
         OR 
        
        bt.res_disease_name LIKE '%COPD%'
         OR 
        
        bt.res_disease_name LIKE '%만성폐쇄성폐질환%'
         OR 
        
        bt.res_disease_name LIKE '%간질성폐질환%'
         OR 
        
        bt.res_disease_name LIKE '%폐섬유화%'
        
        
      )

    UNION

    -- 제외 조건: 파라미터로 받은 약물들
    SELECT DISTINCT pd.user_id
    FROM prescribed_drug pd
    WHERE (
        
        pd.res_drug_name LIKE '%리툭시맙%'
         OR 
        
        pd.res_drug_name LIKE '%에쿨리주맙%'
         OR 
        
        pd.res_drug_name LIKE '%라불리주맙%'
         OR 
        
        pd.res_drug_name LIKE '%efgartigimod%'
         OR 
        
        pd.res_drug_name LIKE '%FcRn%'
         OR 
        
        pd.res_drug_name LIKE '%ibrutinib%'
         OR 
        
        pd.res_drug_name LIKE '%acalabrutinib%'
         OR 
        
        pd.res_drug_name LIKE '%와파린%'
         OR 
        
        pd.res_drug_name LIKE '%NOAC%'
         OR 
        
        pd.res_drug_name LIKE '%아픽사반%'
         OR 
        
        pd.res_drug_name LIKE '%리바록사반%'
        
        
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