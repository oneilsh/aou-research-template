-- Per-person condition counts, grouped by the two most populous gender concepts.
-- We deliberately do NOT hardcode gender_concept_id values: the local Eunomia
-- fixture uses the standard OMOP concepts (8507 MALE / 8532 FEMALE), but the AoU
-- CDR uses its own gender-identity concepts (e.g. 45878463 / 45880669). Picking
-- the top two by population and labeling them via the `concept` table keeps this
-- one query portable across both backends and guarantees exactly two groups.
-- (Note: gender_concept_id is gender identity; for sex at birth a real analysis
-- would use sex_at_birth_concept_id instead.)
-- person_id is returned for per-person grouping in R only; it must never be printed/displayed.
WITH top_genders AS (
  SELECT gender_concept_id
  FROM person
  WHERE gender_concept_id IS NOT NULL AND gender_concept_id <> 0
  GROUP BY gender_concept_id
  ORDER BY COUNT(*) DESC
  LIMIT 2
)
SELECT person_id, grp, n_conditions
FROM (
  SELECT
    p.person_id,
    c.concept_name AS grp,
    COUNT(co.condition_occurrence_id) AS n_conditions
  FROM person p
  JOIN top_genders g ON g.gender_concept_id = p.gender_concept_id
  JOIN concept c ON c.concept_id = p.gender_concept_id
  LEFT JOIN condition_occurrence co ON co.person_id = p.person_id
  GROUP BY p.person_id, c.concept_name
) t;
