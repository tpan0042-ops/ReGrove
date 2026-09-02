#!/usr/bin/env python3
"""Load Victorian EVC context for explicit postcodes from official WFS layers."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import subprocess
import sys
import time
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


WFS_URL = "https://opendata.maps.vic.gov.au/geoserver/wfs"
PAGE_SIZE = 5000
DEFAULT_STATEMENT_TIMEOUT_SECONDS = 180
MAX_STATEMENT_TIMEOUT_SECONDS = 3600
DATASETS = {
    1750: {
        "type_name": "open-data-platform:nv1750_evcbcs",
        "source": {
            "name": "DEECA NV1750 EVC with Bioregional Conservation Status",
            "provider": "Victorian Department of Energy, Environment and Climate Action",
            "url": ("https://discover.data.vic.gov.au/dataset/native-vegetation-modelled-"
                    "1750-ecological-vegetation-classes-with-bioregional-conservation-sta"),
            "licence": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "version": "DataVic WFS layer nv1750_evcbcs; accessed 2026-08-31",
        },
    },
    2005: {
        "type_name": "open-data-platform:nv2005_evcbcs",
        "source": {
            "name": "DEECA NV2005 EVC with Bioregional Conservation Status",
            "provider": "Victorian Department of Energy, Environment and Climate Action",
            "url": ("https://discover.data.vic.gov.au/dataset/native-vegetation-modelled-"
                    "2005-ecological-vegetation-classes-with-bioregional-conservation-sta"),
            "licence": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "version": "DataVic WFS layer nv2005_evcbcs; accessed 2026-08-31",
        },
    },
}
PROPERTIES = "veg_code,x_evcname,evc_bcs_desc,evc_code,bioregion,bioregion_code,geom"


def curl_json(url: str) -> dict:
    """Fetch one WFS page with bounded retries and network timeouts."""
    last_error = "curl request failed"
    for attempt in range(3):
        completed = subprocess.run(
            [
                os.getenv("CURL", "curl"), "--fail", "--location", "--silent",
                "--show-error", "--connect-timeout", "30", "--max-time", "180",
                "--user-agent", "ReGrove-ingestion/1", url,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            try:
                return json.loads(completed.stdout)
            except json.JSONDecodeError as error:
                last_error = f"invalid JSON response: {error}"
        else:
            last_error = completed.stderr.strip() or "curl request failed"
        if attempt < 2:
            delay = 2 ** attempt
            LOG.warning("WFS request failed (attempt %s/3); retrying in %ss: %s",
                        attempt + 1, delay, last_error)
            time.sleep(delay)
    raise RuntimeError(last_error)


def database_postcodes(
    config: DatabaseConfig,
    requested: list[str] | None,
) -> list[tuple[str, str]]:
    condition = ""
    variables: dict[str, object] = {}
    if requested:
        condition = "WHERE postcode = ANY(string_to_array(:'postcodes', ','))"
        variables["postcodes"] = ",".join(requested)
    result = run_psql(
        config,
        f"""
        SELECT postcode || '|' ||
               ST_XMin(Box2D(geometry)) || ',' || ST_YMin(Box2D(geometry)) || ',' ||
               ST_XMax(Box2D(geometry)) || ',' || ST_YMax(Box2D(geometry)) || ',EPSG:4326'
        FROM postcode
        {condition}
        ORDER BY postcode;
        """,
        variables=variables,
    )
    rows = [tuple(line.split("|", 1)) for line in result.splitlines() if line]
    if requested and {row[0] for row in rows} != set(requested):
        missing = sorted(set(requested) - {row[0] for row in rows})
        raise ValueError(f"postcodes not loaded: {', '.join(missing)}")
    if not rows:
        raise ValueError("no postcode rows selected")
    return rows


def fetch_postcode(
    year: int,
    postcode: str,
    bbox: str,
    cache_dir: Path,
    *,
    refresh: bool,
    offline: bool,
) -> Path:
    destination = cache_dir / str(year) / f"{postcode}.geojson"
    if destination.exists() and not refresh:
        cached = json.loads(destination.read_text(encoding="utf-8"))
        if cached.get("regrove_bbox") != bbox:
            raise ValueError(f"cached bbox changed for {postcode}; rerun with --refresh")
        LOG.info("Using cached %s EVC response for %s", year, postcode)
        return destination
    if offline:
        raise FileNotFoundError(f"missing offline cache {destination}")

    features: list[dict] = []
    expected: int | None = None
    start = 0
    while expected is None or start < expected:
        query = urlencode(
            {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeNames": DATASETS[year]["type_name"],
                "propertyName": PROPERTIES,
                "bbox": bbox,
                "count": PAGE_SIZE,
                "startIndex": start,
                "srsName": "EPSG:4326",
                "outputFormat": "application/json",
            }
        )
        page = curl_json(f"{WFS_URL}?{query}")
        if page.get("type") != "FeatureCollection":
            raise ValueError(f"WFS did not return a FeatureCollection for {postcode}")
        if expected is None:
            expected = int(page.get("numberMatched", len(page.get("features", []))))
        returned = page.get("features", [])
        features.extend(returned)
        if not returned:
            break
        start += len(returned)
    if expected is None or len(features) != expected:
        raise ValueError(f"WFS expected {expected} features for {postcode}, received {len(features)}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".geojson.part")
    temporary.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "regrove_bbox": bbox,
                "regrove_number_matched": expected,
                "features": features,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    temporary.replace(destination)
    LOG.info("Cached %s %s EVC features for %s", expected, year, postcode)
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


def read_and_validate(
    path: Path,
    *,
    unclassified: list[str] | None = None,
) -> list[tuple[str, str, str, str, dict]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("type") != "FeatureCollection":
        raise ValueError("input must be a GeoJSON FeatureCollection")
    rows: list[tuple[str, str, str, str, dict]] = []
    feature_ids: set[str] = set()
    metadata: dict[str, tuple[str, str]] = {}
    for index, feature in enumerate(document.get("features", []), start=1):
        properties = feature.get("properties") or {}
        feature_id = str(feature.get("id", "")).strip()
        code = str(properties.get("veg_code", "")).strip()
        name = str(properties.get("x_evcname", "")).strip()
        status = str(properties.get("evc_bcs_desc") or "").strip()
        geometry = feature.get("geometry") or {}
        if not feature_id or feature_id in feature_ids:
            raise ValueError(f"feature {index} has missing/duplicate source id {feature_id!r}")
        if not code or not name:
            if (not code and not name and not status and
                    not str(properties.get("evc_code", "")).strip() and
                    not str(properties.get("bioregion", "")).strip() and
                    not str(properties.get("bioregion_code", "")).strip()):
                if unclassified is not None:
                    unclassified.append(feature_id)
                feature_ids.add(feature_id)
                continue
            raise ValueError(f"feature {feature_id} has missing veg_code/x_evcname")
        if code in metadata and metadata[code] != (name, status):
            raise ValueError(f"inconsistent name/status for regional EVC {code}")
        if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"feature {feature_id} is not polygon geometry")
        pairs = list(_coordinate_pairs(geometry.get("coordinates")))
        if not pairs or any(not (140 <= x <= 151 and -40 <= y <= -33) for x, y in pairs):
            raise ValueError(f"feature {feature_id} has implausible EPSG:4326 coordinates")
        feature_ids.add(feature_id)
        metadata[code] = (name, status)
        rows.append((feature_id, code, name, status, geometry))
    return rows


def _copy_csv(rows: list[tuple]) -> str:
    output = io.StringIO()
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue()


def aggregate_postcode(
    config: DatabaseConfig,
    postcode: str,
    rows: list[tuple[str, str, str, str, dict]],
    statement_timeout_seconds: int = DEFAULT_STATEMENT_TIMEOUT_SECONDS,
) -> tuple[list[dict], set[str], set[str]]:
    if not 1 <= statement_timeout_seconds <= MAX_STATEMENT_TIMEOUT_SECONDS:
        raise ValueError(
            f"statement timeout must be between 1 and {MAX_STATEMENT_TIMEOUT_SECONDS} seconds"
        )
    csv_rows = [
        (feature_id, code, name, status, json.dumps(geometry, separators=(",", ":")))
        for feature_id, code, name, status, geometry in rows
    ]
    sql = rf"""
BEGIN;
SET LOCAL statement_timeout = '{statement_timeout_seconds}s';
CREATE TEMP TABLE evc_stage (
    feature_id text PRIMARY KEY, evc_code text NOT NULL, evc_name text NOT NULL,
    conservation_status text, geometry_json jsonb NOT NULL
) ON COMMIT DROP;
\copy evc_stage FROM STDIN WITH (FORMAT csv)
{_copy_csv(csv_rows)}\.
CREATE TEMP TABLE evc_clean ON COMMIT DROP AS
SELECT *,
       ST_Multi(ST_CollectionExtract(ST_MakeValid(source_geometry), 3)) AS geometry
FROM (
    SELECT feature_id, evc_code, evc_name, conservation_status,
           ST_SetSRID(ST_GeomFromGeoJSON(geometry_json::text), 4326) AS source_geometry
    FROM evc_stage
) parsed;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM evc_clean
        WHERE evc_code = '' OR evc_name = '' OR geometry IS NULL
           OR ST_SRID(geometry) <> 4326
    ) THEN RAISE EXCEPTION 'EVC geometry/field validation failed'; END IF;
END $$;
WITH evc_usable AS MATERIALIZED (
    SELECT *, ST_CollectionExtract(
        ST_MakeValid(ST_Transform(geometry, 3577)), 3
    ) AS metric_geometry
    FROM evc_clean
    WHERE NOT ST_IsEmpty(geometry) AND ST_Area(geometry) > 0
      AND ST_IsValid(geometry) AND GeometryType(geometry) = 'MULTIPOLYGON'
), p AS MATERIALIZED (
    SELECT ST_Transform(geometry, 3577) AS geometry
    FROM postcode WHERE postcode = :'postcode'
), intersections AS (
    SELECT e.evc_code, e.evc_name, e.conservation_status, p.geometry AS postcode_geometry,
           ST_Intersection(p.geometry, e.metric_geometry) AS overlap_geometry
    FROM evc_usable e CROSS JOIN p
    WHERE e.geometry && ST_Transform(p.geometry, 4326)
      AND ST_IsValid(e.metric_geometry)
      AND NOT ST_IsEmpty(e.metric_geometry)
      AND ST_Area(e.metric_geometry) > 0
      AND GeometryType(e.metric_geometry) = 'MULTIPOLYGON'
      AND ST_Intersects(e.geometry, ST_Transform(p.geometry, 4326))
), aggregated AS (
    SELECT evc_code, evc_name, conservation_status, postcode_geometry,
           sum(ST_Area(overlap_geometry)) AS overlap_area
    FROM intersections
    WHERE NOT ST_IsEmpty(overlap_geometry) AND ST_Area(overlap_geometry) > 0
    GROUP BY evc_code, evc_name, conservation_status, postcode_geometry
)
SELECT json_build_object(
    'relationships', COALESCE((
        SELECT json_agg(json_build_object(
            'code', evc_code, 'name', evc_name, 'status', conservation_status,
            'overlap_percent', round((100 * overlap_area /
                NULLIF(ST_Area(postcode_geometry), 0))::numeric, 2)
        ) ORDER BY evc_code) FROM aggregated
    ), '[]'::json),
    'repairs', COALESCE((
        SELECT json_agg(feature_id ORDER BY feature_id)
        FROM evc_clean
        WHERE NOT ST_IsValid(source_geometry)
           OR NOT ST_IsValid(ST_Transform(geometry, 3577))
    ), '[]'::json),
    'unusable', COALESCE((
        SELECT json_agg(feature_id ORDER BY feature_id)
        FROM evc_clean
        WHERE ST_IsEmpty(geometry) OR ST_Area(geometry) <= 0
           OR NOT ST_IsValid(geometry) OR GeometryType(geometry) <> 'MULTIPOLYGON'
    ), '[]'::json)
)::text;
ROLLBACK;
"""
    result = json.loads(run_psql(config, sql, variables={"postcode": postcode}).splitlines()[-1])
    return result["relationships"], set(result["repairs"]), set(result["unusable"])


def write_results(
    config: DatabaseConfig,
    source_id: int,
    year: int,
    selected_postcodes: list[str],
    relationships: list[tuple[str, str, str, str, object]],
) -> tuple[int, int]:
    metadata: dict[str, tuple[str, str]] = {}
    for postcode, code, name, status, overlap_percent in relationships:
        if code in metadata and metadata[code] != (name, status):
            raise ValueError(f"inconsistent name/status for regional EVC {code}")
        if not 0 <= float(overlap_percent) <= 100:
            raise ValueError(
                f"invalid overlap percentage for postcode {postcode}, EVC {code}: "
                f"{overlap_percent}"
            )
        metadata[code] = (name, status)
    classes = sorted({(code, name, status) for _, code, name, status, _ in relationships})
    sql = rf"""
BEGIN;
CREATE TEMP TABLE selected_postcode (postcode text PRIMARY KEY) ON COMMIT DROP;
\copy selected_postcode FROM STDIN WITH (FORMAT csv)
{_copy_csv([(postcode,) for postcode in selected_postcodes])}\.
CREATE TEMP TABLE evc_class_stage (
    evc_code text PRIMARY KEY, evc_name text NOT NULL, conservation_status text
) ON COMMIT DROP;
\copy evc_class_stage FROM STDIN WITH (FORMAT csv)
{_copy_csv(classes)}\.
CREATE TEMP TABLE relationship_stage (
    postcode text, evc_code text, evc_name text, conservation_status text,
    overlap_percent numeric(5, 2), PRIMARY KEY (postcode, evc_code)
) ON COMMIT DROP;
\copy relationship_stage FROM STDIN WITH (FORMAT csv)
{_copy_csv(relationships)}\.
INSERT INTO evc_class (source_id, evc_code, evc_name, conservation_status)
SELECT {source_id}, evc_code, evc_name, NULLIF(conservation_status, '')
FROM evc_class_stage
ON CONFLICT (source_id, evc_code) DO UPDATE SET
    evc_name = EXCLUDED.evc_name,
    conservation_status = EXCLUDED.conservation_status;
DELETE FROM postcode_evc_context context
USING selected_postcode selected
WHERE context.postcode = selected.postcode
  AND context.source_id = {source_id}
  AND context.reference_year = {year};
INSERT INTO postcode_evc_context (
    postcode, evc_id, source_id, reference_year, overlap_percent
)
SELECT r.postcode, e.evc_id, {source_id}, {year}, r.overlap_percent
FROM relationship_stage r
JOIN evc_class e ON e.source_id = {source_id} AND e.evc_code = r.evc_code;
SELECT (SELECT count(*) FROM evc_class WHERE source_id = {source_id}) || '|' ||
       (SELECT count(*) FROM postcode_evc_context c
        JOIN selected_postcode s USING (postcode)
        WHERE c.source_id = {source_id} AND c.reference_year = {year});
COMMIT;
"""
    result = run_psql(config, sql).splitlines()[-1].split("|")
    return int(result[0]), int(result[1])


def run_dataset(
    config: DatabaseConfig,
    year: int,
    postcodes: list[tuple[str, str]],
    args: argparse.Namespace,
) -> None:
    source_id = register_source(config, DATASETS[year]["source"])
    load_id = start_data_load(
        config, source_id, f"EVC {year} context requested for {len(postcodes)} postcodes"
    )
    received = 0
    repaired: set[str] = set()
    unusable: set[str] = set()
    unclassified: set[str] = set()
    all_relationships: list[tuple[str, str, str, str, object]] = []
    try:
        for index, (postcode, bbox) in enumerate(postcodes, start=1):
            path = fetch_postcode(
                year, postcode, bbox, args.cache_dir,
                refresh=args.refresh, offline=args.offline,
            )
            postcode_unclassified: list[str] = []
            rows = read_and_validate(path, unclassified=postcode_unclassified)
            unclassified.update(postcode_unclassified)
            received += len(rows) + len(postcode_unclassified)
            relationships, postcode_repairs, postcode_unusable = aggregate_postcode(
                config, postcode, rows, args.statement_timeout_seconds
            )
            repaired.update(postcode_repairs)
            unusable.update(postcode_unusable)
            all_relationships.extend(
                (postcode, item["code"], item["name"], item["status"], item["overlap_percent"])
                for item in relationships
            )
            LOG.info("EVC %s postcode %s (%s/%s): %s relationships", year, postcode,
                     index, len(postcodes), len(relationships))
        class_count, relationship_count = write_results(
            config, source_id, year, [row[0] for row in postcodes], all_relationships
        )
        no_intersection = len(postcodes) - len({row[0] for row in all_relationships})
        finish_data_load(
            config, load_id, status="complete", received=received,
            accepted=received, rejected=0,
            notes=(f"Scoped EVC {year} load: {class_count} source classes stored, "
                   f"{relationship_count} postcode relationships, {no_intersection} selected "
                   f"postcodes without mapped intersection, {len(repaired)} unique source "
                   f"features repaired with ST_MakeValid, {len(unusable)} unusable source "
                   f"features excluded after repair, {len(unclassified)} explicitly "
                   "unclassified source features excluded; areas calculated in EPSG:3577"),
        )
        LOG.info("EVC %s complete: classes=%s relationships=%s no_intersection=%s repairs=%s",
                 year, class_count, relationship_count, no_intersection, len(repaired))
    except (KeyboardInterrupt, SystemExit) as error:
        finish_data_load(
            config, load_id, status="interrupted", received=received or None,
            accepted=None, rejected=None,
            notes=f"Interrupted before completion: {type(error).__name__}",
        )
        raise
    except Exception as error:
        LOG.exception("EVC %s load %s failed", year, load_id)
        finish_data_load(
            config, load_id, status="failed", received=received or None,
            accepted=0 if received else None, rejected=received or None,
            notes=f"Failed: {error}",
        )
        raise


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--postcode", action="append", help="postcode to process; repeatable")
    scope.add_argument("--all-postcodes", action="store_true", help="process every loaded postcode")
    parser.add_argument("--period", choices=("1750", "2005", "both"), default="both")
    parser.add_argument(
        "--cache-dir", type=Path,
        default=Path.home() / ".cache" / "regrove" / "evc",
    )
    parser.add_argument("--offline", action="store_true", help="require existing cache files")
    parser.add_argument("--refresh", action="store_true", help="replace matching cache files")
    parser.add_argument(
        "--statement-timeout-seconds", type=int,
        default=DEFAULT_STATEMENT_TIMEOUT_SECONDS,
        help=(f"per-postcode PostgreSQL timeout (1-{MAX_STATEMENT_TIMEOUT_SECONDS}s; "
              f"default {DEFAULT_STATEMENT_TIMEOUT_SECONDS})"),
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    if not 1 <= args.statement_timeout_seconds <= MAX_STATEMENT_TIMEOUT_SECONDS:
        parser.error(
            f"--statement-timeout-seconds must be between 1 and {MAX_STATEMENT_TIMEOUT_SECONDS}"
        )
    return args


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)
    config = DatabaseConfig.from_environment()
    postcodes = database_postcodes(config, None if args.all_postcodes else args.postcode)
    years = (1750, 2005) if args.period == "both" else (int(args.period),)
    for year in years:
        run_dataset(config, year, postcodes, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
