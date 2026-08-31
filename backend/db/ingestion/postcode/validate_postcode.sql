\set ON_ERROR_STOP on

-- Run with: psql ... -v postcode=3233 -f validate_postcode.sql
SELECT
    postcode,
    source_id,
    ST_GeometryType(geometry) AS geometry_type,
    ST_SRID(geometry) AS srid,
    ST_IsValid(geometry) AS geometry_is_valid,
    round(ST_Area(geometry::geography) / 1000000)::bigint AS approximate_area_sq_km,
    ST_AsText(ST_PointOnSurface(geometry)) AS representative_point
FROM postcode
WHERE postcode = :'postcode';
