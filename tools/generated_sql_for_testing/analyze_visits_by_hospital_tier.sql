-- Generated from: analyze_visits_by_hospital_tier.yaml
-- Parameters used: {'disease_keyword': '당뇨병', 'snapshot_dt': '2025-09-01'}

-- 특정 질환의 병원급별(1차/2차/3차) 방문 현황 분석
-- 파라미터: disease_keyword = 당뇨병

SELECT
  hospital_type,
  COUNT(*) AS total_visits,
  COUNT(DISTINCT user_id) AS unique_patient_count
FROM (
  SELECT
    bt.user_id,
    CASE
      WHEN SUBSTRING(bt.res_hospital_code, 3, 1) = '1' THEN '3차'
      WHEN SUBSTRING(bt.res_hospital_code, 3, 1) = '2' THEN '2차'
      WHEN SUBSTRING(bt.res_hospital_code, 3, 1) = '3' THEN '1차'
      ELSE NULL
    END AS hospital_type
  FROM basic_treatment bt
  WHERE bt.deleted = FALSE
    AND bt.res_disease_name LIKE '%당뇨병%'
    AND bt.res_hospital_code IS NOT NULL
    AND SUBSTRING(bt.res_hospital_code, 3, 1) IN ('1', '2', '3')
) AS categorized_data
WHERE hospital_type IS NOT NULL
GROUP BY hospital_type
ORDER BY
  CASE hospital_type
    WHEN '1차' THEN 1
    WHEN '2차' THEN 2
    WHEN '3차' THEN 3
    ELSE 4
  END;