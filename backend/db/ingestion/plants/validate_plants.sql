\set ON_ERROR_STOP on

-- Database taxonomy/trait view. Original-name resolution remains in the loader's
-- CSV report because the approved v1 schema has no source-name mapping table.
WITH vicflora_source AS (
    SELECT source_id
    FROM source
    WHERE source_name = 'VicFlora taxonomy'
      AND version LIKE 'GraphQL API 1.0.0; accessed %'
    ORDER BY version DESC, source_id DESC
    LIMIT 1
), plant_rows AS (
    SELECT p.plant_species_id, p.scientific_name, p.common_name, p.native_status,
           jsonb_object_agg(t.trait_name, t.trait_value ORDER BY t.trait_name)
               FILTER (WHERE t.plant_trait_id IS NOT NULL) AS source_backed_traits
    FROM vicflora_source s
    JOIN plant_trait t ON t.source_id = s.source_id
    JOIN plant_species p ON p.plant_species_id = t.plant_species_id
    GROUP BY p.plant_species_id
)
SELECT scientific_name, common_name, native_status, source_backed_traits
FROM plant_rows
ORDER BY scientific_name;

SELECT s.source_name, s.provider, s.url, s.licence, s.version,
       d.load_id, d.started_at, d.completed_at, d.status,
       d.rows_received, d.rows_accepted, d.rows_rejected, d.notes
FROM source s
LEFT JOIN data_load d ON d.source_id = s.source_id
WHERE s.source_name = 'VicFlora taxonomy'
ORDER BY s.source_id, d.load_id;

SELECT p.scientific_name, t.trait_name, t.source_id, count(*) AS duplicate_count
FROM plant_trait t
JOIN plant_species p ON p.plant_species_id = t.plant_species_id
JOIN source s ON s.source_id = t.source_id
WHERE s.source_name = 'VicFlora taxonomy'
GROUP BY p.scientific_name, t.trait_name, t.source_id
HAVING count(*) > 1;
