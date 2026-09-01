#!/usr/bin/env python3
"""Load local VBA 1-minute flora or fauna SHP data for explicit postcodes."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

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


DATASETS = {
    "flora": {
        "layer": "VBA_FLORA_GRID_1M",
        "source_name": "Victorian Biodiversity Atlas flora - 1 minute grid summary",
        "url": ("https://discover.data.vic.gov.au/dataset/"
                "victorian-biodiversity-atlas-flora-1-minute-grid-summary"),
        "fields": {
            "CELL_ID": "Integer64", "TAXON_ID": "Integer64",
            "SCI_NAME": "String", "COMM_NAME": "String", "RECORDS": "Integer64",
            "FIRST_DATE": "Date", "FIRST_YEAR": "String", "LAST_DATE": "Date",
            "LAST_YEAR": "String", "VIC_LF": "String", "TAXON_TYPE": "String",
            "FFG_DESC": "String", "EPBC_DESC": "String", "ORIGIN": "String",
            "VERS_DATE": "String",
        },
    },
    "fauna": {
        "layer": "VBA_FAUNA_GRID_1M",
        "source_name": "Victorian Biodiversity Atlas fauna - 1 minute grid summary",
        "url": ("https://discover.data.vic.gov.au/dataset/"
                "victorian-biodiversity-atlas-fauna-1-minute-grid-summary"),
        "fields": {
            "CELL_ID": "Integer64", "TAXON_ID": "Integer64",
            "SCI_NAME": "String", "COMM_NAME": "String", "RECORDS": "Integer64",
            "FIRST_DATE": "Date", "FIRST_YEAR": "String", "LAST_DATE": "Date",
            "LAST_YEAR": "String", "TAXON_TYPE": "String", "FFG_DESC": "String",
            "EPBC_DESC": "String", "ORIGIN": "String", "VERS_DATE": "String",
        },
    },
}
PROVIDER = "Victorian Department of Energy, Environment and Climate Action"
LICENCE = "Creative Commons Attribution 4.0 International (CC BY 4.0)"
FIELD_RE = re.compile(
    r"^([A-Z][A-Z0-9_]*): ([A-Za-z0-9]+)(?: \(|$)", re.MULTILINE,
)
REPORT_FIELDS = [
    "dataset", "postcode", "taxon_id", "scientific_name", "common_name",
    "resolution_result", "source_feature_count", "record_count",
    "first_record_date", "last_record_date", "notes",
]


def inspect_shapefile(path: Path, dataset: str) -> dict[str, object]:
    if path.suffix.casefold() != ".shp":
        raise ValueError("--input must identify the .shp file")
    missing = [str(path.with_suffix(ext)) for ext in (".shp", ".dbf", ".shx", ".prj")
               if not path.with_suffix(ext).is_file()]
    if missing:
        raise FileNotFoundError("missing required shapefile components: " + ", ".join(missing))
    completed = subprocess.run(
        [os.getenv("OGRINFO", "ogrinfo"), "-ro", "-so", "-al", str(path)],
        text=True, capture_output=True, check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "ogrinfo failed")
    output = completed.stdout
    expected = DATASETS[dataset]
    layer = re.search(r"^Layer name: (.+)$", output, re.MULTILINE)
    geometry = re.search(r"^Geometry: (.+)$", output, re.MULTILINE)
    count = re.search(r"^Feature Count: ([0-9]+)$", output, re.MULTILINE)
    if not layer or layer.group(1).strip() != expected["layer"]:
        raise ValueError(f"expected layer {expected['layer']!r}")
    if not geometry or geometry.group(1).strip() not in {"Polygon", "Multi Polygon"}:
        raise ValueError("VBA layer must contain polygon geometry")
    if not count:
        raise ValueError("ogrinfo did not report a feature count")
    if not re.search(r'ID\["EPSG",4283\]', output):
        raise ValueError("VBA layer must declare GDA94 / EPSG:4283")
    actual_fields = dict(FIELD_RE.findall(output))
    if actual_fields != expected["fields"]:
        raise ValueError(
            f"unexpected {dataset} schema; expected {expected['fields']}, got {actual_fields}"
        )
    return {
        "layer": layer.group(1).strip(),
        "geometry": geometry.group(1).strip(),
        "feature_count": int(count.group(1)),
        "crs": "EPSG:4283",
        "fields": actual_fields,
    }


def postcode_bbox(config: DatabaseConfig, postcodes: list[str]) -> tuple[float, float, float, float]:
    result = run_psql(
        config,
        """
        WITH selected AS (
            SELECT ST_Transform(geometry, 4283) AS geometry
            FROM postcode
            WHERE postcode = ANY(string_to_array(:'postcodes', ','))
        )
        SELECT ST_XMin(extent) || '|' || ST_YMin(extent) || '|' ||
               ST_XMax(extent) || '|' || ST_YMax(extent)
        FROM (SELECT ST_Extent(geometry) AS extent FROM selected) bounds
        WHERE extent IS NOT NULL;
        """,
        variables={"postcodes": ",".join(postcodes)},
    )
    if not result:
        raise ValueError("none of the requested postcodes is loaded")
    loaded = run_psql(
        config,
        "SELECT postcode FROM postcode WHERE postcode = ANY(string_to_array(:'postcodes', ','));",
        variables={"postcodes": ",".join(postcodes)},
    ).splitlines()
    missing = sorted(set(postcodes) - set(loaded))
    if missing:
        raise ValueError("postcodes not loaded: " + ", ".join(missing))
    return tuple(float(value) for value in result.split("|"))  # type: ignore[return-value]


def extract_bbox_features(path: Path, dataset: str, bbox: tuple[float, ...]) -> list[dict]:
    fields = ",".join(DATASETS[dataset]["fields"])
    command = [
        os.getenv("OGR2OGR", "ogr2ogr"), "-f", "GeoJSONSeq", "/vsistdout/", str(path),
        "-spat", *(str(value) for value in bbox), "-spat_srs", "EPSG:4283",
        "-t_srs", "EPSG:4326", "-select", fields,
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "ogr2ogr extraction failed")
    rows = []
    seen: set[tuple[int, int]] = set()
    for line_number, line in enumerate(completed.stdout.splitlines(), 1):
        if not line.strip("\x1e \t"):
            continue
        feature = json.loads(line.lstrip("\x1e"))
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        try:
            cell_id = int(properties["CELL_ID"])
            taxon_id = int(properties["TAXON_ID"])
            records = int(properties["RECORDS"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"feature {line_number} has invalid identifier/count fields") from exc
        key = (cell_id, taxon_id)
        if key in seen:
            raise ValueError(f"duplicate CELL_ID/TAXON_ID source row {key}")
        seen.add(key)
        scientific_name = " ".join(str(properties.get("SCI_NAME") or "").split())
        common_name = " ".join(str(properties.get("COMM_NAME") or "").split())
        if not scientific_name or records <= 0:
            raise ValueError(f"feature {line_number} has blank name or non-positive RECORDS")
        first = parse_date(properties.get("FIRST_DATE"), line_number, "FIRST_DATE")
        last = parse_date(properties.get("LAST_DATE"), line_number, "LAST_DATE")
        if (first is None) != (last is None) or (first and last and first > last):
            raise ValueError(f"feature {line_number} has inconsistent first/last dates")
        if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"feature {line_number} has non-polygon geometry")
        versions = "" if properties.get("VERS_DATE") is None else str(properties["VERS_DATE"])
        if not versions.strip():
            raise ValueError(f"feature {line_number} has no VERS_DATE")
        rows.append({
            "stage_id": len(rows) + 1, "cell_id": cell_id, "taxon_id": taxon_id,
            "scientific_name": scientific_name, "common_name": common_name,
            "record_count": records, "first_date": first, "last_date": last,
            "version": versions.strip(), "geometry": geometry,
        })
    if not rows:
        raise ValueError("source has no features in the selected postcode bounding box")
    versions = {row["version"] for row in rows}
    if len(versions) != 1:
        raise ValueError(f"selected source rows contain multiple VERS_DATE values: {versions}")
    return rows


def parse_date(value: object, line_number: int, field: str) -> date | None:
    if value in (None, "", "0000-00-00", "0000/00/00"):
        return None
    try:
        return date.fromisoformat(str(value).replace("/", "-"))
    except ValueError as exc:
        raise ValueError(f"feature {line_number} has invalid {field}: {value!r}") from exc


def _copy_csv(rows: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    for row in rows:
        writer.writerow((
            row["stage_id"], row["cell_id"], row["taxon_id"],
            row["scientific_name"], row["common_name"], row["record_count"],
            row["first_date"] or "", row["last_date"] or "", row["version"],
            json.dumps(row["geometry"], separators=(",", ":")),
        ))
    return output.getvalue()


def load_rows(
    config: DatabaseConfig,
    dataset: str,
    source_id: int,
    postcodes: list[str],
    rows: list[dict],
) -> dict:
    taxonomy_sql = flora_sql(source_id) if dataset == "flora" else fauna_sql(source_id)
    sql = rf"""
BEGIN;
CREATE TEMP TABLE vba_stage (
    stage_id integer PRIMARY KEY, cell_id bigint NOT NULL, taxon_id bigint NOT NULL,
    scientific_name text NOT NULL, common_name text, record_count integer NOT NULL,
    first_date date, last_date date, version text NOT NULL, geometry_json jsonb NOT NULL,
    UNIQUE (cell_id, taxon_id)
) ON COMMIT DROP;
\copy vba_stage FROM STDIN WITH (FORMAT csv)
{_copy_csv(rows)}\.
CREATE TEMP TABLE vba_clean ON COMMIT DROP AS
SELECT *, ST_SetSRID(ST_GeomFromGeoJSON(geometry_json::text), 4326) AS geometry
FROM vba_stage;
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM vba_clean
        WHERE record_count <= 0 OR scientific_name = '' OR geometry IS NULL
           OR ST_IsEmpty(geometry) OR NOT ST_IsValid(geometry)
           OR GeometryType(geometry) NOT IN ('POLYGON', 'MULTIPOLYGON')
           OR ST_SRID(geometry) <> 4326
           OR (first_date IS NULL) <> (last_date IS NULL)
           OR first_date > last_date
    ) THEN RAISE EXCEPTION 'VBA stage validation failed'; END IF;
END $$;
CREATE TEMP TABLE vba_intersection ON COMMIT DROP AS
SELECT DISTINCT p.postcode, s.stage_id
FROM postcode p
JOIN vba_clean s ON ST_Intersects(p.geometry, s.geometry)
WHERE p.postcode = ANY(string_to_array(:'postcodes', ','));
CREATE TEMP TABLE vba_taxon_quality ON COMMIT DROP AS
WITH names AS (
    SELECT DISTINCT taxon_id, scientific_name FROM vba_clean
), per_id AS (
    SELECT taxon_id, count(*) AS names_per_id FROM names GROUP BY taxon_id
), per_name AS (
    SELECT scientific_name, count(*) AS ids_per_name FROM names GROUP BY scientific_name
)
SELECT n.taxon_id, n.scientific_name,
       CASE WHEN names_per_id > 1 OR ids_per_name > 1
            THEN 'ambiguous_source_taxon' ELSE 'source_identity_ok' END AS identity_status
FROM names n JOIN per_id USING (taxon_id) JOIN per_name USING (scientific_name);
{taxonomy_sql}
CREATE TEMP TABLE vba_local_report ON COMMIT DROP AS
SELECT i.postcode, s.taxon_id, s.scientific_name,
       min(NULLIF(s.common_name, '')) AS common_name,
       c.resolution_result,
       count(DISTINCT s.stage_id) AS source_feature_count,
       sum(s.record_count)::bigint AS record_count,
       min(s.first_date) AS first_record_date,
       max(s.last_date) AS last_record_date,
       c.notes
FROM vba_intersection i
JOIN vba_clean s USING (stage_id)
JOIN vba_taxon_class c USING (taxon_id, scientific_name)
GROUP BY i.postcode, s.taxon_id, s.scientific_name, c.resolution_result, c.notes;
SELECT jsonb_build_object(
    'source_features_fetched', (SELECT count(*) FROM vba_clean),
    'intersecting_features', (SELECT count(DISTINCT stage_id) FROM vba_intersection),
    'distinct_intersecting_taxa', (SELECT count(*) FROM vba_local_report),
    'accepted_features', (
        SELECT count(DISTINCT i.stage_id) FROM vba_intersection i
        JOIN vba_clean s USING (stage_id)
        JOIN vba_taxon_class c USING (taxon_id, scientific_name)
        WHERE c.loadable
    ),
    'persisted_summaries', (SELECT count(*) FROM vba_local_report r
                            JOIN vba_taxon_class c USING (taxon_id, scientific_name)
                            WHERE c.loadable),
    'taxa', COALESCE((SELECT jsonb_agg(to_jsonb(r) ORDER BY postcode, scientific_name)
                      FROM vba_local_report r), '[]'::jsonb)
)::text;
COMMIT;
"""
    result = run_psql(
        config, sql,
        variables={"source_id": source_id, "postcodes": ",".join(postcodes)},
    )
    return json.loads(result.splitlines()[-1])


def flora_sql(source_id: int) -> str:
    return rf"""
CREATE TEMP TABLE vba_taxon_class ON COMMIT DROP AS
SELECT q.taxon_id, q.scientific_name,
       CASE
         WHEN q.identity_status <> 'source_identity_ok' THEN 'ambiguous_source_taxon'
         WHEN p.plant_species_id IS NULL THEN 'unmatched_vicflora_taxon'
         ELSE 'exact_vicflora_match'
       END AS resolution_result,
       p.plant_species_id,
       q.identity_status = 'source_identity_ok' AND p.plant_species_id IS NOT NULL AS loadable,
       CASE
         WHEN q.identity_status <> 'source_identity_ok' THEN 'source taxon ID/name is ambiguous'
         WHEN p.plant_species_id IS NULL THEN 'no exact existing VicFlora-backed PLANT_SPECIES name'
         ELSE ''
       END AS notes
FROM vba_taxon_quality q
LEFT JOIN plant_species p
  ON p.scientific_name = q.scientific_name
 AND EXISTS (
     SELECT 1 FROM plant_trait t JOIN source vs USING (source_id)
     WHERE t.plant_species_id = p.plant_species_id
       AND vs.source_name = 'VicFlora taxonomy'
 );
DELETE FROM plant_occurrence_summary
WHERE source_id = {source_id}
  AND postcode = ANY(string_to_array(:'postcodes', ','));
INSERT INTO plant_occurrence_summary (
    postcode, plant_species_id, source_id, source_taxon_id, record_count,
    latest_record_date, period_start, period_end
)
SELECT i.postcode, c.plant_species_id, {source_id}, s.taxon_id::text,
       sum(s.record_count)::bigint, max(s.last_date), min(s.first_date), max(s.last_date)
FROM vba_intersection i
JOIN vba_clean s USING (stage_id)
JOIN vba_taxon_class c USING (taxon_id, scientific_name)
WHERE c.loadable
GROUP BY i.postcode, c.plant_species_id, s.taxon_id;
"""


def fauna_sql(source_id: int) -> str:
    return rf"""
CREATE TEMP TABLE vba_taxon_class ON COMMIT DROP AS
SELECT q.taxon_id, q.scientific_name,
       CASE WHEN q.identity_status = 'source_identity_ok'
            THEN 'accepted_vba_taxon' ELSE 'ambiguous_source_taxon' END AS resolution_result,
       NULL::bigint AS plant_species_id,
       q.identity_status = 'source_identity_ok' AS loadable,
       CASE WHEN q.identity_status = 'source_identity_ok' THEN ''
            ELSE 'source taxon ID/name is ambiguous' END AS notes
FROM vba_taxon_quality q;
INSERT INTO fauna_species (scientific_name, common_name)
SELECT s.scientific_name, min(NULLIF(s.common_name, ''))
FROM vba_clean s
JOIN vba_intersection i USING (stage_id)
JOIN vba_taxon_class c USING (taxon_id, scientific_name)
WHERE c.loadable
GROUP BY s.scientific_name
ON CONFLICT (scientific_name) DO UPDATE SET
    common_name = COALESCE(fauna_species.common_name, EXCLUDED.common_name);
DELETE FROM fauna_occurrence_summary
WHERE source_id = {source_id}
  AND postcode = ANY(string_to_array(:'postcodes', ','));
INSERT INTO fauna_occurrence_summary (
    postcode, fauna_species_id, source_id, record_count,
    latest_record_date, period_start, period_end
)
SELECT i.postcode, f.fauna_species_id, {source_id}, sum(s.record_count)::integer,
       max(s.last_date), min(s.first_date), max(s.last_date)
FROM vba_intersection i
JOIN vba_clean s USING (stage_id)
JOIN vba_taxon_class c USING (taxon_id, scientific_name)
JOIN fauna_species f USING (scientific_name)
WHERE c.loadable
GROUP BY i.postcode, f.fauna_species_id;
"""


def write_report(path: Path, dataset: str, taxa: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        for row in taxa:
            writer.writerow({"dataset": dataset, **row})
    temporary.replace(path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--postcode", action="append", required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)
    report = args.report or (
        Path.home() / ".cache/regrove/vba" / f"{args.dataset}-resolution-report.csv"
    )
    config = DatabaseConfig.from_environment()
    load_id = None
    try:
        metadata = inspect_shapefile(args.input, args.dataset)
        bbox = postcode_bbox(config, args.postcode)
        rows = extract_bbox_features(args.input, args.dataset, bbox)
        version = str(rows[0]["version"])
        source = {
            "name": DATASETS[args.dataset]["source_name"], "provider": PROVIDER,
            "url": DATASETS[args.dataset]["url"], "licence": LICENCE,
            "version": f"VBA VERS_DATE {version}",
        }
        source_id = register_source(config, source)
        load_id = start_data_load(
            config, source_id,
            f"Local official SHP {args.input.name}; accessed={date.today().isoformat()}; "
            f"postcodes={','.join(args.postcode)}; "
            "grid-intersection occurrence context; RECORDS is not abundance",
        )
        result = load_rows(config, args.dataset, source_id, args.postcode, rows)
        write_report(report, args.dataset, result["taxa"])
        accepted = int(result["accepted_features"])
        finish_data_load(
            config, load_id, status="complete", received=len(rows), accepted=accepted,
            rejected=len(rows) - accepted,
            notes=(f"source_features={metadata['feature_count']}; bbox_features={len(rows)}; "
                   f"intersecting_features={result['intersecting_features']}; "
                   f"distinct_intersecting_taxa={result['distinct_intersecting_taxa']}; "
                   f"persisted_summaries={result['persisted_summaries']}; report={report}; "
                   "full cell RECORDS assigned as area-level context without overlap weighting"),
        )
        counts = Counter(row["resolution_result"] for row in result["taxa"])
        LOG.info("%s", json.dumps({**result, "taxa": None, "resolution_counts": counts}))
        LOG.info("Taxon report: %s", report)
        return 0
    except Exception as exc:
        LOG.exception("VBA %s load failed", args.dataset)
        if load_id is not None:
            finish_data_load(
                config, load_id, status="failed", received=None, accepted=None,
                rejected=None, notes=f"Failed: {exc}",
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
