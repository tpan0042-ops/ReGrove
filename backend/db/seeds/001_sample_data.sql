-- SAMPLE DATA ONLY. These records verify relationships; they are not ecological claims.
BEGIN;

INSERT INTO source (source_name, provider, version, licence)
VALUES
    ('SAMPLE postcode boundaries', 'TEST DATA ONLY', 'sample-v1', 'Not for production'),
    ('SAMPLE bioregions', 'TEST DATA ONLY', 'sample-v1', 'Not for production'),
    ('SAMPLE Victorian EVC', 'TEST DATA ONLY', 'sample-v1', 'Not for production'),
    ('SAMPLE fauna occurrence', 'TEST DATA ONLY', 'sample-v1', 'Not for production'),
    ('SAMPLE fauna traits', 'TEST DATA ONLY', 'sample-v1', 'Not for production'),
    ('SAMPLE wildlife guidance', 'TEST DATA ONLY', 'sample-v1', 'Not for production'),
    ('SAMPLE plant traits', 'TEST DATA ONLY', 'sample-v1', 'Not for production')
ON CONFLICT (source_name, version) DO NOTHING;

INSERT INTO data_load (
    source_id, started_at, completed_at, status,
    rows_received, rows_accepted, rows_rejected, notes
)
SELECT s.source_id, v.started_at, v.completed_at, 'sample_complete', 2, 2, 0,
       'SAMPLE ingestion audit record; not a real source load.'
FROM source s
CROSS JOIN (VALUES
    ('2026-01-01 00:00:00+00'::timestamptz, '2026-01-01 00:00:01+00'::timestamptz),
    ('2026-01-02 00:00:00+00'::timestamptz, '2026-01-02 00:00:01+00'::timestamptz)
) AS v(started_at, completed_at)
WHERE s.source_name = 'SAMPLE fauna occurrence'
  AND NOT EXISTS (
      SELECT 1 FROM data_load d
      WHERE d.source_id = s.source_id AND d.started_at = v.started_at
  );

INSERT INTO postcode (postcode, geometry, source_id)
SELECT '3233',
       ST_Multi(ST_GeomFromText('POLYGON((143.70 -38.80,143.80 -38.80,143.80 -38.70,143.70 -38.70,143.70 -38.80))', 4326)),
       source_id
FROM source
WHERE source_name = 'SAMPLE postcode boundaries'
ON CONFLICT (postcode) DO NOTHING;

INSERT INTO bioregion (bioregion_name, geometry, source_id)
SELECT 'SAMPLE bioregion',
       ST_Multi(ST_GeomFromText('POLYGON((143.60 -38.90,143.90 -38.90,143.90 -38.60,143.60 -38.60,143.60 -38.90))', 4326)),
       source_id
FROM source
WHERE source_name = 'SAMPLE bioregions'
ON CONFLICT (source_id, bioregion_name) DO NOTHING;

INSERT INTO postcode_bioregion (postcode, bioregion_id, overlap_percent)
SELECT '3233', bioregion_id, 100.00
FROM bioregion
WHERE bioregion_name = 'SAMPLE bioregion'
ON CONFLICT (postcode, bioregion_id) DO NOTHING;

INSERT INTO evc_class (evc_code, evc_name, conservation_status, source_id)
SELECT 'SAMPLE-EVC-1', 'SAMPLE vegetation community', 'SAMPLE ONLY', source_id
FROM source
WHERE source_name = 'SAMPLE Victorian EVC'
ON CONFLICT (source_id, evc_code) DO NOTHING;

INSERT INTO postcode_evc_context (postcode, evc_id, source_id, reference_year, overlap_percent)
SELECT '3233', e.evc_id, s.source_id, 1750, 75.00
FROM evc_class e
JOIN source s ON s.source_name = 'SAMPLE Victorian EVC'
WHERE e.evc_code = 'SAMPLE-EVC-1'
ON CONFLICT (postcode, evc_id, source_id, reference_year) DO NOTHING;

INSERT INTO fauna_species (scientific_name, common_name, taxon_group)
VALUES
    ('SAMPLE fauna alpha', 'SAMPLE small bird', 'bird'),
    ('SAMPLE fauna beta', 'SAMPLE nectar bird', 'bird')
ON CONFLICT (scientific_name) DO NOTHING;

INSERT INTO fauna_occurrence_summary (
    postcode, fauna_species_id, source_id, record_count, latest_record_date,
    period_start, period_end
)
SELECT '3233', f.fauna_species_id, s.source_id,
       CASE f.scientific_name WHEN 'SAMPLE fauna alpha' THEN 12 ELSE 5 END,
       CASE f.scientific_name WHEN 'SAMPLE fauna alpha' THEN DATE '2026-01-15' ELSE DATE '2026-01-10' END,
       DATE '2025-01-01',
       CASE f.scientific_name WHEN 'SAMPLE fauna alpha' THEN DATE '2026-01-15' ELSE DATE '2026-01-10' END
FROM fauna_species f
JOIN source s ON s.source_name = 'SAMPLE fauna occurrence'
WHERE f.scientific_name IN ('SAMPLE fauna alpha', 'SAMPLE fauna beta')
ON CONFLICT (
    postcode, fauna_species_id, source_id, period_start, period_end
) DO NOTHING;

INSERT INTO fauna_trait (fauna_species_id, source_id, trait_name, trait_value)
SELECT f.fauna_species_id, s.source_id, v.trait_name, v.trait_value
FROM (VALUES
    ('SAMPLE fauna alpha', 'sample_diet_component', 'invertebrates'),
    ('SAMPLE fauna beta', 'sample_diet_component', 'nectar')
) AS v(scientific_name, trait_name, trait_value)
JOIN fauna_species f USING (scientific_name)
JOIN source s ON s.source_name = 'SAMPLE fauna traits'
WHERE NOT EXISTS (
    SELECT 1 FROM fauna_trait t
    WHERE t.fauna_species_id = f.fauna_species_id
      AND t.source_id = s.source_id
      AND t.trait_name = v.trait_name
      AND t.trait_value = v.trait_value
);

INSERT INTO fauna_guild (guild_name, description)
VALUES
    ('SAMPLE small insectivorous birds', 'TEST guild only'),
    ('SAMPLE nectar-feeding birds', 'TEST guild only')
ON CONFLICT (guild_name) DO NOTHING;

INSERT INTO fauna_guild_membership (fauna_species_id, fauna_guild_id, membership_role)
SELECT f.fauna_species_id, g.fauna_guild_id, v.membership_role
FROM (VALUES
    ('SAMPLE fauna alpha', 'SAMPLE small insectivorous birds', 'primary'),
    ('SAMPLE fauna alpha', 'SAMPLE nectar-feeding birds', 'secondary'),
    ('SAMPLE fauna beta', 'SAMPLE nectar-feeding birds', 'primary')
) AS v(scientific_name, guild_name, membership_role)
JOIN fauna_species f USING (scientific_name)
JOIN fauna_guild g USING (guild_name)
ON CONFLICT (fauna_species_id, fauna_guild_id) DO NOTHING;

INSERT INTO fauna_garden_relevance (
    fauna_species_id, source_id, relevance_status, rationale, reviewed_at, rule_version
)
SELECT f.fauna_species_id, s.source_id, 'candidate',
       'SAMPLE relevance only; not an ecological classification.',
       '2026-01-20 00:00:00+00'::timestamptz, 'sample-v1'
FROM fauna_species f
JOIN source s ON s.source_name = 'SAMPLE wildlife guidance'
WHERE f.scientific_name = 'SAMPLE fauna alpha'
ON CONFLICT (fauna_species_id) DO UPDATE SET
    source_id = EXCLUDED.source_id,
    relevance_status = EXCLUDED.relevance_status,
    rationale = EXCLUDED.rationale,
    reviewed_at = EXCLUDED.reviewed_at,
    rule_version = EXCLUDED.rule_version;

INSERT INTO habitat_requirement (requirement_name, description)
VALUES
    ('SAMPLE dense refuge', 'TEST habitat requirement only'),
    ('SAMPLE nectar resource', 'TEST habitat requirement only')
ON CONFLICT (requirement_name) DO NOTHING;

INSERT INTO guild_habitat_rule (
    fauna_guild_id, habitat_requirement_id, source_id, status, evidence
)
SELECT g.fauna_guild_id, h.habitat_requirement_id, s.source_id,
       'validated_for_coarse_use', 'SAMPLE evidence only; not an ecological claim.'
FROM (VALUES
    ('SAMPLE small insectivorous birds', 'SAMPLE dense refuge'),
    ('SAMPLE nectar-feeding birds', 'SAMPLE nectar resource')
) AS v(guild_name, requirement_name)
JOIN fauna_guild g USING (guild_name)
JOIN habitat_requirement h USING (requirement_name)
JOIN source s ON s.source_name = 'SAMPLE wildlife guidance'
ON CONFLICT (fauna_guild_id, habitat_requirement_id, source_id) DO NOTHING;

INSERT INTO plant_species (scientific_name, common_name, native_status)
VALUES
    ('SAMPLE plant alpha', 'SAMPLE dense shrub', 'SAMPLE ONLY'),
    ('SAMPLE plant beta', 'SAMPLE nectar shrub', 'SAMPLE ONLY')
ON CONFLICT (scientific_name) DO NOTHING;

INSERT INTO plant_trait (plant_species_id, source_id, trait_name, trait_value)
SELECT p.plant_species_id, s.source_id, v.trait_name, v.trait_value
FROM (VALUES
    ('SAMPLE plant alpha', 'sample_foliage_density', 'dense'),
    ('SAMPLE plant alpha', 'sample_foliage_density', 'very_dense'),
    ('SAMPLE plant beta', 'sample_resource', 'nectar')
) AS v(scientific_name, trait_name, trait_value)
JOIN plant_species p USING (scientific_name)
JOIN source s ON s.source_name = 'SAMPLE plant traits'
WHERE NOT EXISTS (
    SELECT 1 FROM plant_trait t
    WHERE t.plant_species_id = p.plant_species_id
      AND t.source_id = s.source_id
      AND t.trait_name = v.trait_name
      AND t.trait_value = v.trait_value
);

INSERT INTO plant_resource_evidence (
    plant_species_id, habitat_requirement_id, source_id, evidence_summary
)
SELECT p.plant_species_id, h.habitat_requirement_id, s.source_id,
       'SAMPLE resource evidence only; does not claim attraction of fauna.'
FROM (VALUES
    ('SAMPLE plant alpha', 'SAMPLE dense refuge'),
    ('SAMPLE plant beta', 'SAMPLE dense refuge'),
    ('SAMPLE plant beta', 'SAMPLE nectar resource')
) AS v(scientific_name, requirement_name)
JOIN plant_species p USING (scientific_name)
JOIN habitat_requirement h USING (requirement_name)
JOIN source s ON s.source_name = 'SAMPLE wildlife guidance'
ON CONFLICT (plant_species_id, habitat_requirement_id, source_id) DO NOTHING;

INSERT INTO local_plant_suitability (
    plant_species_id, bioregion_id, source_id, suitability_status, evidence_summary
)
SELECT p.plant_species_id, b.bioregion_id, s.source_id,
       'sample_candidate', 'SAMPLE regional evidence only; not parcel-level suitability.'
FROM plant_species p
CROSS JOIN bioregion b
JOIN source s ON s.source_name = 'SAMPLE bioregions'
WHERE p.scientific_name IN ('SAMPLE plant alpha', 'SAMPLE plant beta')
  AND b.bioregion_name = 'SAMPLE bioregion'
ON CONFLICT (plant_species_id, bioregion_id, source_id) DO NOTHING;

COMMIT;
