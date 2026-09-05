\set ON_ERROR_STOP on

-- Run after loading the official Victorian VBIOREG100 source:
-- psql ... -v postcode=3233 -f validate_bioregion.sql
WITH current_bioregion_source AS (
    SELECT source_id
    FROM source
    WHERE source_name = 'DEECA Victorian Bioregions 1:100,000'
      AND version LIKE 'VBIOREG100 version 3.0%'
    ORDER BY version DESC, source_id DESC
    LIMIT 1
)
SELECT
    relationship.postcode,
    b.bioregion_id,
    b.bioregion_name,
    relationship.overlap_percent,
    ST_SRID(b.geometry) AS bioregion_srid,
    ST_IsValid(b.geometry) AS bioregion_geometry_is_valid,
    round((
        ST_Area(
            ST_Intersection(
                ST_Transform(p.geometry, 3577),
                ST_Transform(b.geometry, 3577)
            )
        ) / 1000000)::numeric,
        3
    ) AS overlap_sq_km
FROM postcode_bioregion relationship
JOIN postcode p USING (postcode)
JOIN bioregion b USING (bioregion_id)
JOIN current_bioregion_source current_source
  ON current_source.source_id = b.source_id
WHERE relationship.postcode = :'postcode'
ORDER BY relationship.overlap_percent DESC, b.bioregion_name;

-- Real examples only: postcodes spanning multiple current Victorian Bioregions.
WITH current_bioregion_source AS (
    SELECT source_id
    FROM source
    WHERE source_name = 'DEECA Victorian Bioregions 1:100,000'
      AND version LIKE 'VBIOREG100 version 3.0%'
    ORDER BY version DESC, source_id DESC
    LIMIT 1
)
SELECT
    relationship.postcode,
    count(*) AS bioregion_count,
    string_agg(b.bioregion_name, '; ' ORDER BY b.bioregion_name) AS bioregions
FROM postcode_bioregion relationship
JOIN bioregion b USING (bioregion_id)
JOIN current_bioregion_source current_source
  ON current_source.source_id = b.source_id
GROUP BY relationship.postcode
HAVING count(*) > 1
ORDER BY count(*) DESC, relationship.postcode
LIMIT 10;
