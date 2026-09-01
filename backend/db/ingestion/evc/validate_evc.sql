\set ON_ERROR_STOP on

-- Run with: psql ... -v postcode=3233 -f validate_evc.sql
-- Ecological results use the newest registered version of each EVC product.
-- Older SOURCE/DATA_LOAD rows remain visible in the provenance audit below.
WITH current_evc_source AS (
    SELECT DISTINCT ON (source_name) source_id, source_name, version
    FROM source
    WHERE source_name IN (
        'DEECA NV1750 EVC with Bioregional Conservation Status',
        'DEECA NV2005 EVC with Bioregional Conservation Status'
    )
    ORDER BY source_name, source_id DESC
)
SELECT
    context.postcode,
    context.reference_year,
    source.source_name,
    source.version AS source_version,
    e.evc_code,
    e.evc_name,
    e.conservation_status,
    context.overlap_percent
FROM postcode_evc_context context
JOIN evc_class e USING (evc_id)
JOIN current_evc_source source ON source.source_id = context.source_id
WHERE context.postcode = :'postcode'
ORDER BY context.reference_year, context.overlap_percent DESC, e.evc_code;

-- Coverage below 100% is retained and reported, not filled or normalised.
WITH current_evc_source AS (
    SELECT DISTINCT ON (source_name) source_id, source_name, version
    FROM source
    WHERE source_name IN (
        'DEECA NV1750 EVC with Bioregional Conservation Status',
        'DEECA NV2005 EVC with Bioregional Conservation Status'
    )
    ORDER BY source_name, source_id DESC
)
SELECT
    context.postcode,
    context.reference_year,
    source.source_name,
    source.version AS source_version,
    count(*) AS regional_evc_count,
    sum(context.overlap_percent) AS mapped_postcode_percent
FROM postcode_evc_context context
JOIN current_evc_source source ON source.source_id = context.source_id
WHERE context.postcode = :'postcode'
GROUP BY context.postcode, context.reference_year, source.source_name, source.version
ORDER BY context.reference_year;

-- Provenance/audit rows for the two EVC products.
SELECT
    source.source_id,
    source.source_name,
    source.provider,
    source.url,
    source.licence,
    source.version,
    source.source_id = max(source.source_id) OVER (
        PARTITION BY source.source_name
    ) AS current_validation_source,
    load.started_at,
    load.completed_at,
    load.status,
    load.rows_received,
    load.rows_accepted,
    load.rows_rejected,
    load.notes
FROM source
JOIN data_load load USING (source_id)
WHERE source.source_name IN (
    'DEECA NV1750 EVC with Bioregional Conservation Status',
    'DEECA NV2005 EVC with Bioregional Conservation Status'
)
ORDER BY load.started_at DESC;
