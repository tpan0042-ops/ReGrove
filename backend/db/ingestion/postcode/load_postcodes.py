#!/usr/bin/env python3
"""Load Victorian ABS ASGS 2021 Postal Area geometry into ReGrove."""

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


SERVICE_URL = "https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/POA/MapServer/0"
QUERY_URL = f"{SERVICE_URL}/query"
EXPECTED_VICTORIAN_POA_COUNT = 694
SOURCE = {
    "name": "ABS ASGS 2021 Postal Areas",
    "provider": "Australian Bureau of Statistics",
    "url": SERVICE_URL,
    "licence": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
    "version": "ASGS Edition 3 (2021)",
}
POSTCODE_RE = re.compile(r"^3[0-9]{3}$")


def download_geojson(destination: Path, refresh: bool = False) -> Path:
    if destination.exists() and not refresh:
        LOG.info("Using cached ABS response: %s", destination)
        return destination

    params = urlencode(
        {
            "where": "poa_code_2021 LIKE '3%'",
            "outFields": (
                "poa_code_2021,poa_name_2021,area_albers_sqkm,"
                "asgs_loci_uri_2021"
            ),
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
        }
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    url = f"{QUERY_URL}?{params}"
    temporary = destination.with_suffix(destination.suffix + ".part")
    LOG.info("Downloading Victorian ABS Postal Areas")
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
            url,
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


def read_and_validate(path: Path, expected_count: int) -> list[tuple[str, dict]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("type") != "FeatureCollection":
        raise ValueError("input must be a GeoJSON FeatureCollection")

    rows: list[tuple[str, dict]] = []
    seen: set[str] = set()
    for index, feature in enumerate(document.get("features", []), start=1):
        properties = feature.get("properties") or {}
        postcode = str(properties.get("poa_code_2021", "")).strip()
        geometry = feature.get("geometry") or {}
        if not POSTCODE_RE.fullmatch(postcode):
            raise ValueError(f"feature {index} has non-Victorian/invalid POA code {postcode!r}")
        if postcode in seen:
            raise ValueError(f"duplicate POA code {postcode!r} in source")
        if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"POA {postcode} is not a polygon geometry")
        pairs = list(_coordinate_pairs(geometry.get("coordinates")))
        if not pairs:
            raise ValueError(f"POA {postcode} has empty geometry")
        if any(not (130 <= x <= 160 and -45 <= y <= -25) for x, y in pairs):
            raise ValueError(f"POA {postcode} coordinates are not plausible EPSG:4326 Australia")
        seen.add(postcode)
        rows.append((postcode, geometry))

    if len(rows) != expected_count:
        raise ValueError(f"expected {expected_count} Victorian POAs, received {len(rows)}")
    return rows


def _copy_csv(rows: list[tuple[str, dict]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    for postcode, geometry in rows:
        writer.writerow((postcode, json.dumps(geometry, separators=(",", ":"))))
    return output.getvalue()


def load_rows(config: DatabaseConfig, source_id: int, rows: list[tuple[str, dict]]) -> int:
    sql = rf"""
BEGIN;
CREATE TEMP TABLE postcode_stage (
    postcode text PRIMARY KEY,
    geometry_json jsonb NOT NULL
) ON COMMIT DROP;
\copy postcode_stage (postcode, geometry_json) FROM STDIN WITH (FORMAT csv)
{_copy_csv(rows)}\.

CREATE TEMP TABLE postcode_clean ON COMMIT DROP AS
SELECT postcode,
       ST_SetSRID(ST_GeomFromGeoJSON(geometry_json::text), 4326) AS geometry
FROM postcode_stage;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM postcode_clean
        WHERE postcode !~ '^3[0-9]{{3}}$'
           OR geometry IS NULL
           OR ST_IsEmpty(geometry)
           OR NOT ST_IsValid(geometry)
           OR GeometryType(geometry) NOT IN ('POLYGON', 'MULTIPOLYGON')
           OR ST_SRID(geometry) <> 4326
    ) THEN
        RAISE EXCEPTION 'postcode staging validation failed';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM postcode_clean incoming
        JOIN postcode existing USING (postcode)
        WHERE existing.source_id <> {source_id}
    ) THEN
        RAISE EXCEPTION 'a postcode already belongs to a different source';
    END IF;
END $$;

INSERT INTO postcode (postcode, geometry, source_id)
SELECT postcode,
       ST_Multi(geometry)::geometry(MultiPolygon, 4326),
       {source_id}
FROM postcode_clean
ON CONFLICT (postcode) DO UPDATE SET
    geometry = EXCLUDED.geometry,
    source_id = EXCLUDED.source_id;

DO $$
BEGIN
    IF (SELECT count(*) FROM postcode WHERE source_id = {source_id}) <> {len(rows)} THEN
        RAISE EXCEPTION 'database/source row count differs from staged row count';
    END IF;
END $$;

SELECT count(*) FROM postcode WHERE source_id = {source_id};
COMMIT;
"""
    result = run_psql(config, sql)
    return int(result.splitlines()[-1])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="cached EPSG:4326 ABS GeoJSON")
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path.home() / ".cache" / "regrove" / "abs_poa_2021_victoria.geojson",
        help="download cache outside the repository",
    )
    parser.add_argument("--refresh", action="store_true", help="replace the cached API response")
    parser.add_argument(
        "--expected-count",
        type=int,
        default=EXPECTED_VICTORIAN_POA_COUNT,
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
    load_id = start_data_load(config, source_id, f"Postcode load requested from {origin}")
    received: int | None = None

    try:
        path = args.input or download_geojson(args.cache, args.refresh)
        rows = read_and_validate(path, args.expected_count)
        received = len(rows)
        accepted = load_rows(config, source_id, rows)
        if accepted != received:
            raise RuntimeError(f"database contains {accepted} source rows after loading {received}")
        finish_data_load(
            config,
            load_id,
            status="complete",
            received=received,
            accepted=accepted,
            rejected=0,
            notes=f"Loaded and validated {accepted} ABS Postal Areas from {path}",
        )
        LOG.info("Load %s complete: received=%s accepted=%s rejected=0", load_id, received, accepted)
        return 0
    except Exception as error:
        LOG.exception("Postcode load %s failed", load_id)
        finish_data_load(
            config,
            load_id,
            status="failed",
            received=received,
            accepted=0 if received is not None else None,
            rejected=received,
            notes=f"Failed: {error}",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
