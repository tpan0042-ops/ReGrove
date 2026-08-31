#!/usr/bin/env python3
"""Load DCCEEW IBRA 7.1 regions and derive postcode overlaps."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import (  # noqa: E402
    LOG,
    DatabaseConfig,
    configure_logging,
    finish_data_load,
    register_source,
    run_psql,
    start_data_load,
)


SERVICE_URL = (
    "https://gis.environment.gov.au/gispubmap/rest/services/ogc_services/"
    "IBRA7_Regions/FeatureServer/0"
)
QUERY_URL = f"{SERVICE_URL}/query"
EXPECTED_REGION_COUNT = 89
SOURCE = {
    "name": "DCCEEW IBRA 7.1 Regions",
    "provider": (
        "Australian Government Department of Climate Change, Energy, "
        "the Environment and Water"
    ),
    "url": SERVICE_URL,
    "licence": "Creative Commons Attribution 3.0 Australia (CC BY 3.0 AU)",
    "version": "IBRA 7.1 (2025)",
}
CODE_RE = re.compile(r"^[A-Z]{3}$")


def download_geojson(destination: Path, refresh: bool = False) -> Path:
    if destination.exists() and not refresh:
        LOG.info("Using cached IBRA response: %s", destination)
        return destination
    params = urlencode(
        {
            "where": "1=1",
            "outFields": "REG_CODE_7,REG_NAME_7,HECTARES",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
        }
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    LOG.info("Downloading DCCEEW IBRA 7.1 regions")
    completed = subprocess.run(
        [
            os.getenv("CURL", "curl"),
            "--fail",
            "--location",
            "--silent",
            "--show-error",
            "--user-agent",
            "ReGrove-ingestion/1",
            "--output",
            str(temporary),
            f"{QUERY_URL}?{params}",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(completed.stderr.strip() or "curl download failed")
    temporary.replace(destination)
    LOG.info("Cached %s bytes at %s", destination.stat().st_size, destination)
    return destination


def _coordinate_pairs(value: object):
    if isinstance(value, list) and len(value) >= 2 and all(
        isinstance(item, (int, float)) for item in value[:2]
    ):
        yield float(value[0]), float(value[1])
        return
    if isinstance(value, list):
        for item in value:
            yield from _coordinate_pairs(item)


def read_and_validate(path: Path, expected_count: int) -> list[tuple[str, str, dict]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("type") != "FeatureCollection":
        raise ValueError("input must be a GeoJSON FeatureCollection")
    if document.get("exceededTransferLimit"):
        raise ValueError("source response exceeded the service transfer limit")

    rows: list[tuple[str, str, dict]] = []
    codes: set[str] = set()
    names: set[str] = set()
    for index, feature in enumerate(document.get("features", []), start=1):
        properties = feature.get("properties") or {}
        code = str(properties.get("REG_CODE_7", "")).strip()
        name = str(properties.get("REG_NAME_7", "")).strip()
        geometry = feature.get("geometry") or {}
        if not CODE_RE.fullmatch(code):
            raise ValueError(f"feature {index} has invalid IBRA region code {code!r}")
        if not name:
            raise ValueError(f"IBRA region {code} has no name")
        if code in codes:
            raise ValueError(f"duplicate IBRA region code {code!r}")
        if name in names:
            raise ValueError(f"duplicate IBRA region name {name!r}")
        if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"IBRA region {code} is not a polygon geometry")
        pairs = list(_coordinate_pairs(geometry.get("coordinates")))
        if not pairs:
            raise ValueError(f"IBRA region {code} has empty geometry")
        if any(not (65 <= x <= 175 and -60 <= y <= -5) for x, y in pairs):
            raise ValueError(f"IBRA region {code} coordinates are not plausible EPSG:4326")
        codes.add(code)
        names.add(name)
        rows.append((code, name, geometry))

    if len(rows) != expected_count:
        raise ValueError(f"expected {expected_count} IBRA regions, received {len(rows)}")
    return rows


def _copy_csv(rows: list[tuple[str, str, dict]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    for code, name, geometry in rows:
        writer.writerow((code, name, json.dumps(geometry, separators=(",", ":"))))
    return output.getvalue()


def load_rows(
    config: DatabaseConfig,
    source_id: int,
    rows: list[tuple[str, str, dict]],
) -> tuple[int, int, int]:
    sql = rf"""
BEGIN;
CREATE TEMP TABLE bioregion_stage (
    region_code text PRIMARY KEY,
    region_name text NOT NULL UNIQUE,
    geometry_json jsonb NOT NULL
) ON COMMIT DROP;
\copy bioregion_stage (region_code, region_name, geometry_json) FROM STDIN WITH (FORMAT csv)
{_copy_csv(rows)}\.

CREATE TEMP TABLE bioregion_clean ON COMMIT DROP AS
SELECT region_code,
       region_name,
       source_geometry,
       ST_Multi(
           ST_CollectionExtract(ST_MakeValid(source_geometry), 3)
       ) AS geometry
FROM (
    SELECT region_code,
           region_name,
           ST_SetSRID(ST_GeomFromGeoJSON(geometry_json::text), 4326)
               AS source_geometry
    FROM bioregion_stage
) parsed
;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM bioregion_clean
        WHERE region_code !~ '^[A-Z]{{3}}$'
           OR region_name = ''
           OR geometry IS NULL
           OR ST_IsEmpty(geometry)
           OR NOT ST_IsValid(geometry)
           OR GeometryType(geometry) <> 'MULTIPOLYGON'
           OR ST_SRID(geometry) <> 4326
    ) THEN
        RAISE EXCEPTION 'IBRA staging validation failed';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM postcode) THEN
        RAISE EXCEPTION 'postcode ingestion must run before bioregion ingestion';
    END IF;
END $$;

INSERT INTO bioregion (source_id, bioregion_name, geometry)
SELECT {source_id}, region_name,
       ST_Multi(geometry)::geometry(MultiPolygon, 4326)
FROM bioregion_clean
ON CONFLICT (source_id, bioregion_name) DO UPDATE SET
    geometry = EXCLUDED.geometry;

DO $$
BEGIN
    IF (SELECT count(*) FROM bioregion WHERE source_id = {source_id}) <> {len(rows)} THEN
        RAISE EXCEPTION 'database/source region count differs from staged row count';
    END IF;
END $$;

CREATE TEMP TABLE postcode_bioregion_stage ON COMMIT DROP AS
WITH transformed AS (
    SELECT p.postcode,
           ST_Transform(p.geometry, 3577) AS postcode_geometry,
           b.bioregion_id,
           ST_Transform(b.geometry, 3577) AS bioregion_geometry
    FROM postcode p
    JOIN bioregion b
      ON b.source_id = {source_id}
     AND ST_Intersects(p.geometry, b.geometry)
), intersections AS (
    SELECT postcode, bioregion_id, postcode_geometry,
           ST_Intersection(postcode_geometry, bioregion_geometry) AS overlap_geometry
    FROM transformed
)
SELECT postcode,
       bioregion_id,
       round((100 * ST_Area(overlap_geometry)
             / NULLIF(ST_Area(postcode_geometry), 0))::numeric, 2)::numeric(5, 2)
           AS overlap_percent
FROM intersections
WHERE NOT ST_IsEmpty(overlap_geometry)
  AND ST_Area(overlap_geometry) > 0;

ALTER TABLE postcode_bioregion_stage
    ADD PRIMARY KEY (postcode, bioregion_id);

DO $$
DECLARE
    postcode_count integer := (SELECT count(*) FROM postcode);
    relationship_count integer := (SELECT count(*) FROM postcode_bioregion_stage);
BEGIN
    IF relationship_count < postcode_count OR relationship_count > postcode_count * 10 THEN
        RAISE EXCEPTION 'implausible postcode-bioregion relationship count: %', relationship_count;
    END IF;
    IF EXISTS (
        SELECT 1 FROM postcode p
        WHERE NOT EXISTS (
            SELECT 1 FROM postcode_bioregion_stage r WHERE r.postcode = p.postcode
        )
    ) THEN
        RAISE EXCEPTION 'one or more postcodes have no positive-area IBRA intersection';
    END IF;
END $$;

DELETE FROM postcode_bioregion relationship
USING bioregion b
WHERE relationship.bioregion_id = b.bioregion_id
  AND b.source_id = {source_id};

INSERT INTO postcode_bioregion (postcode, bioregion_id, overlap_percent)
SELECT postcode, bioregion_id, overlap_percent
FROM postcode_bioregion_stage;

SELECT (SELECT count(*) FROM bioregion WHERE source_id = {source_id})
       || '|' ||
       (SELECT count(*) FROM postcode_bioregion relationship
        JOIN bioregion b USING (bioregion_id)
        WHERE b.source_id = {source_id})
       || '|' ||
       (SELECT count(*) FROM bioregion_clean WHERE NOT ST_IsValid(source_geometry));
COMMIT;
"""
    result = run_psql(config, sql)
    region_count, relationship_count, repaired_count = result.splitlines()[-1].split("|")
    return int(region_count), int(relationship_count), int(repaired_count)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="cached EPSG:4326 DCCEEW GeoJSON")
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path.home() / ".cache" / "regrove" / "ibra_7_1_regions.geojson",
        help="download cache outside the repository",
    )
    parser.add_argument("--refresh", action="store_true", help="replace the cached API response")
    parser.add_argument(
        "--expected-count", type=int, default=EXPECTED_REGION_COUNT,
        help="version-specific row-count guard",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)
    config = DatabaseConfig.from_environment()
    source_id = register_source(config, SOURCE)
    origin = args.input or args.cache
    load_id = start_data_load(config, source_id, f"IBRA region load requested from {origin}")
    received: int | None = None
    try:
        path = args.input or download_geojson(args.cache, args.refresh)
        rows = read_and_validate(path, args.expected_count)
        received = len(rows)
        accepted, relationship_count, repaired_count = load_rows(config, source_id, rows)
        finish_data_load(
            config, load_id, status="complete", received=received,
            accepted=accepted, rejected=0,
            notes=(f"Loaded {accepted} IBRA 7.1 regions from {path}; repaired "
                   f"{repaired_count} invalid source geometries with ST_MakeValid; derived "
                   f"{relationship_count} positive-area postcode relationships in EPSG:3577"),
        )
        LOG.info(
            "Load %s complete: regions=%s repaired=%s relationships=%s rejected=0",
            load_id, accepted, repaired_count, relationship_count,
        )
        return 0
    except Exception as error:
        LOG.exception("IBRA region load %s failed", load_id)
        finish_data_load(
            config, load_id, status="failed", received=received,
            accepted=0 if received is not None else None, rejected=received,
            notes=f"Failed: {error}",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
