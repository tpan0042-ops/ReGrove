\set ON_ERROR_STOP on

-- Run with: psql ... -v postcode=3233 -f validate_vba.sql
SELECT 'flora' AS dataset,
       count(*) AS persisted_taxa,
       sum(record_count) AS observation_record_count,
       min(period_start) AS first_record_date,
       max(period_end) AS last_record_date
FROM plant_occurrence_summary o
JOIN source s USING (source_id)
WHERE o.postcode = :'postcode'
  AND s.source_name = 'Victorian Biodiversity Atlas flora - 1 minute grid summary'
  AND s.version LIKE 'VBA VERS_DATE %'
UNION ALL
SELECT 'fauna', count(*), sum(record_count)::bigint,
       min(period_start), max(period_end)
FROM fauna_occurrence_summary o
JOIN source s USING (source_id)
WHERE o.postcode = :'postcode'
  AND s.source_name = 'Victorian Biodiversity Atlas fauna - 1 minute grid summary'
  AND s.version LIKE 'VBA VERS_DATE %';

SELECT 'flora' AS dataset, p.scientific_name, p.common_name,
       o.record_count AS observation_record_count,
       o.period_start AS first_record_date, o.period_end AS last_record_date
FROM plant_occurrence_summary o
JOIN plant_species p USING (plant_species_id)
JOIN source s USING (source_id)
WHERE o.postcode = :'postcode'
  AND s.source_name = 'Victorian Biodiversity Atlas flora - 1 minute grid summary'
  AND s.version LIKE 'VBA VERS_DATE %'
UNION ALL
SELECT 'fauna', f.scientific_name, f.common_name, o.record_count,
       o.period_start, o.period_end
FROM fauna_occurrence_summary o
JOIN fauna_species f USING (fauna_species_id)
JOIN source s USING (source_id)
WHERE o.postcode = :'postcode'
  AND s.source_name = 'Victorian Biodiversity Atlas fauna - 1 minute grid summary'
  AND s.version LIKE 'VBA VERS_DATE %'
ORDER BY observation_record_count DESC, scientific_name
LIMIT 30;

SELECT s.source_name, s.provider, s.url, s.licence, s.version,
       d.load_id, d.started_at, d.completed_at, d.status,
       d.rows_received, d.rows_accepted, d.rows_rejected, d.notes
FROM source s
JOIN data_load d USING (source_id)
WHERE s.source_name IN (
    'Victorian Biodiversity Atlas flora - 1 minute grid summary',
    'Victorian Biodiversity Atlas fauna - 1 minute grid summary'
)
ORDER BY d.load_id;

SELECT 'flora' AS dataset, postcode, plant_species_id AS species_id,
       source_id, source_taxon_id, period_start, period_end, count(*) AS duplicates
FROM plant_occurrence_summary
GROUP BY postcode, plant_species_id, source_id, source_taxon_id, period_start, period_end
HAVING count(*) > 1
UNION ALL
SELECT 'fauna', postcode, fauna_species_id, source_id, NULL,
       period_start, period_end, count(*)
FROM fauna_occurrence_summary
GROUP BY postcode, fauna_species_id, source_id, period_start, period_end
HAVING count(*) > 1;

\echo 'Interpretation: record counts are documented observations/monitoring effort, not abundance.'
\echo 'A missing row does not prove absence; intersecting 1-minute-grid evidence is not property-level.'
\echo 'Flora occurrence does not establish planting suitability.'
