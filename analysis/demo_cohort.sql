-- Per-person condition counts, grouped by recorded sex.
-- Standard OMOP gender concepts: 8507 = MALE, 8532 = FEMALE.
-- Unqualified table names resolve on local DuckDB (Eunomia) and, with a default
-- dataset set on the BigQuery connection, on the AoU CDR. (See GETTING_STARTED
-- for the AoU dialect note.)
-- person_id is returned for per-person grouping in R only; it must never be printed/displayed.
SELECT person_id, grp, n_conditions
FROM (
  SELECT
    p.person_id,
    CASE WHEN p.gender_concept_id = 8507 THEN 'male' ELSE 'female' END AS grp,
    COUNT(co.condition_occurrence_id) AS n_conditions
  FROM person p
  LEFT JOIN condition_occurrence co ON co.person_id = p.person_id
  WHERE p.gender_concept_id IN (8507, 8532)
  GROUP BY p.person_id, p.gender_concept_id
) t;
