-- Generated from: get_detailed_visit_list_by_disease.yaml
-- Parameters used: {'disease_keyword': '당뇨병', 'snapshot_dt': '2025-09-01'}

-- 특정 질환을 가진 환자들의 상세 방문 기록 추출
-- 파라미터: disease_keyword = 당뇨병

SELECT
    ip.name                       AS patient_name,
    ip.birthday                   AS birthday,
    bt.res_treat_start_date       AS visit_date,
    bt.res_hospital_name          AS diagnosis_hospital,
    h.full_address                AS hospital_address,
    CASE
        WHEN h.medical_facility_type_code IN ('01','1') THEN '3차'
        WHEN h.medical_facility_type_code IN ('11','21','28','29','41','92') THEN '2차'
        ELSE '1차'
    END                           AS hospital_grade,
    COLLECT_SET(pd.res_drug_name)       AS prescribed_drugs,
    COLLECT_SET(pd.res_ingredients)     AS prescribed_ingredients,
    u.phone_number                AS phone_number
FROM `basic_treatment` bt
LEFT JOIN `hospital` h
       ON bt.res_hospital_code = h.hospital_code
LEFT JOIN `prescribed_drug` pd
       ON bt.user_id = pd.user_id
      AND bt.res_treat_start_date = pd.res_treat_start_date
LEFT JOIN `user` u
       ON bt.user_id = u.id
LEFT JOIN `insured_person` ip
       ON ip.user_id = bt.user_id
WHERE bt.deleted = FALSE
  AND bt.res_disease_name LIKE CONCAT('%', '당뇨병', '%')
GROUP BY
    ip.name,
    ip.birthday,
    bt.res_treat_start_date,
    bt.res_hospital_name,
    h.full_address,
    hospital_grade,
    u.phone_number
ORDER BY ip.name, bt.res_treat_start_date DESC;