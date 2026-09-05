#!/usr/bin/env python3
"""Resolve a reviewed plant-name list against VicFlora and load species taxonomy."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
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


GRAPHQL_URL = "https://vicflora.rbg.vic.gov.au/graphql"
SOURCE = {
    "name": "VicFlora taxonomy",
    "provider": "Royal Botanic Gardens Victoria, National Herbarium of Victoria",
    "url": GRAPHQL_URL,
    "licence": "VicFlora text/data CC BY 4.0; API documentation Apache 2.0",
    "version": f"GraphQL API 1.0.0; accessed {date.today().isoformat()}",
}
CONTROLLED_TRAITS = {
    "taxonomic_status": "accepted_taxonomic_status",
    "occurrence_status": "occurrence_status",
    "establishment_means": "establishment_means",
    "degree_of_establishment": "degree_of_establishment",
    "endemic_to_victoria": "endemic_to_victoria",
    "has_introduced_occurrences": "has_introduced_occurrences",
    "epbc_status": "epbc_status",
    "ffg_status": "ffg_status",
}
REPORT_FIELDS = [
    "original_name", "query_name", "accepted_name", "accepted_taxon_id",
    "accepted_rank", "common_name", "native_status", "resolution_result",
    "source_taxonomic_status", "accepted_taxonomic_status", "occurrence_status", "establishment_means",
    "degree_of_establishment", "endemic_to_victoria",
    "has_introduced_occurrences", "epbc_status", "ffg_status", "notes",
]
CONCEPT_FIELDS = """
id taxonRank taxonomicStatus occurrenceStatus establishmentMeans
degreeOfEstablishment endemic hasIntroducedOccurrences epbc ffg
taxonName { fullName }
preferredVernacularName { name }
"""


def normalise_name(value: str) -> str:
    """Normalise whitespace only; spelling and taxonomic qualifiers are preserved."""
    return " ".join(value.split())


def read_name_list(path: Path) -> list[dict[str, str]]:
    """Read original names, with an optional tab-separated reviewed query name."""
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for line_number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) > 2:
            raise ValueError(f"line {line_number}: expected original_name[tab]query_name")
        original = normalise_name(parts[0])
        query = normalise_name(parts[1] if len(parts) == 2 else parts[0])
        if not original or not query:
            raise ValueError(f"line {line_number}: plant names cannot be blank")
        key = (original.casefold(), query.casefold())
        duplicate = key in seen
        seen.add(key)
        rows.append({"original_name": original, "query_name": query, "duplicate": duplicate})
    if not rows:
        raise ValueError("the reviewed plant-name list is empty")
    return rows


def _graphql_query(names: list[str]) -> str:
    selections = []
    for index, name in enumerate(names):
        selections.append(
            f'n{index}: taxonNameAutocomplete(q: {json.dumps(name)}) {{ '
            f'id fullName rank taxonConcepts {{ {CONCEPT_FIELDS} '
            f'acceptedConcept {{ {CONCEPT_FIELDS} }} }} }}'
        )
    return "query { " + " ".join(selections) + " }"


def fetch_names(names: list[str]) -> dict[str, list[dict]]:
    if not names:
        return {}
    payload = json.dumps({"query": _graphql_query(names)})
    completed = subprocess.run(
        [
            os.getenv("CURL", "curl"), "--fail", "--location", "--silent",
            "--show-error", "--user-agent", "ReGrove-ingestion/1",
            "--header", "content-type: application/json", "--data-binary", "@-",
            GRAPHQL_URL,
        ],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "VicFlora request failed")
    document = json.loads(completed.stdout)
    if document.get("errors"):
        raise RuntimeError(f"VicFlora GraphQL errors: {document['errors']}")
    data = document.get("data") or {}
    return {name: data.get(f"n{index}") or [] for index, name in enumerate(names)}


def load_cache(
    path: Path,
    names: list[str],
    *,
    refresh: bool,
    offline: bool,
    batch_size: int = 100,
) -> dict[str, list[dict]]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    document: dict = {}
    if path.exists():
        document = json.loads(path.read_text(encoding="utf-8"))
        if document.get("endpoint") != GRAPHQL_URL:
            raise ValueError(f"cache endpoint does not match {GRAPHQL_URL}")
    responses = document.get("responses") or {}
    missing = names if refresh else [name for name in names if name not in responses]
    if missing and offline:
        raise FileNotFoundError(f"offline cache is missing {len(missing)} plant names")
    for start in range(0, len(missing), batch_size):
        batch = missing[start:start + batch_size]
        LOG.info(
            "Resolving VicFlora names %s-%s of %s",
            start + 1, start + len(batch), len(missing),
        )
        responses.update(fetch_names(batch))
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".part")
        temporary.write_text(
            json.dumps({"endpoint": GRAPHQL_URL, "responses": responses}, separators=(",", ":")),
            encoding="utf-8",
        )
        temporary.replace(path)
    return responses


def _blank_report(original: str, query: str, result: str, notes: str) -> dict[str, object]:
    row: dict[str, object] = {field: "" for field in REPORT_FIELDS}
    row.update(
        original_name=original,
        query_name=query,
        resolution_result=result,
        notes=notes,
    )
    return row


def map_native_status(concept: dict) -> str:
    occurrence = concept.get("occurrenceStatus")
    means = concept.get("establishmentMeans")
    degree = concept.get("degreeOfEstablishment")
    introduced = concept.get("hasIntroducedOccurrences")
    if occurrence == "PRESENT" and means == "NATIVE" and degree == "NATIVE":
        if introduced is True:
            return "Victorian native; introduced occurrences also recorded"
        return "Victorian native"
    if occurrence == "PRESENT" and means == "INTRODUCED":
        return "Victorian introduced"
    return ""


def resolve_name(original: str, query: str, candidates: list[dict]) -> dict[str, object]:
    exact_names = [
        item for item in candidates
        if normalise_name(str(item.get("fullName") or "")).casefold() == query.casefold()
    ]
    if not exact_names:
        return _blank_report(original, query, "unresolved", "no exact VicFlora taxon-name match")

    paths: list[tuple[dict, dict]] = []
    for taxon_name in exact_names:
        for concept in taxon_name.get("taxonConcepts") or []:
            accepted = concept.get("acceptedConcept")
            if not accepted and concept.get("taxonomicStatus") == "ACCEPTED":
                accepted = concept
            if accepted and accepted.get("id") and accepted.get("taxonName", {}).get("fullName"):
                paths.append((concept, accepted))

    accepted_ids = {accepted["id"] for _, accepted in paths}
    if not paths:
        return _blank_report(original, query, "unresolved", "exact name has no accepted concept")
    if len(accepted_ids) != 1:
        names = sorted({path[1].get("taxonName", {}).get("fullName", "") for path in paths})
        return _blank_report(
            original, query, "ambiguous", "multiple accepted concepts: " + "; ".join(names)
        )

    source, accepted = paths[0]
    rank = accepted.get("taxonRank") or ""
    accepted_name = accepted.get("taxonName", {}).get("fullName") or ""
    source_status = source.get("taxonomicStatus") or ""
    result = "exact_accepted"
    if source_status != "ACCEPTED" or accepted_name.casefold() != query.casefold():
        result = "synonym_resolved"
    if rank != "SPECIES":
        result = "non_species_rank"

    common = (accepted.get("preferredVernacularName") or {}).get("name") or ""
    row = _blank_report(original, query, result, "")
    row.update(
        accepted_name=accepted_name,
        accepted_taxon_id=accepted.get("id") or "",
        accepted_rank=rank,
        common_name=common,
        native_status=map_native_status(accepted),
        source_taxonomic_status=source_status,
        accepted_taxonomic_status=accepted.get("taxonomicStatus") or "",
        occurrence_status=accepted.get("occurrenceStatus") or "",
        establishment_means=accepted.get("establishmentMeans") or "",
        degree_of_establishment=accepted.get("degreeOfEstablishment") or "",
        endemic_to_victoria=_display_value(accepted.get("endemic")),
        has_introduced_occurrences=_display_value(accepted.get("hasIntroducedOccurrences")),
        epbc_status=accepted.get("epbc") or "",
        ffg_status=accepted.get("ffg") or "",
    )
    if result == "non_species_rank":
        row["notes"] = "accepted concept is not species rank; not loaded into v1"
    elif query != original:
        row["notes"] = "query name supplied by reviewed input; original preserved in report"
    return row


def _display_value(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "" if value is None else str(value)


def resolve_rows(inputs: list[dict[str, str]], responses: dict[str, list[dict]]) -> list[dict]:
    results = []
    for item in inputs:
        if item["duplicate"]:
            results.append(_blank_report(
                item["original_name"], item["query_name"], "duplicate_input",
                "duplicate original/query pair; first occurrence retained",
            ))
        else:
            results.append(resolve_name(
                item["original_name"], item["query_name"], responses[item["query_name"]]
            ))
    return results


def write_report(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _copy_csv(rows: list[tuple]) -> str:
    output = io.StringIO()
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue()


def rows_for_database(results: list[dict]) -> tuple[list[tuple], list[tuple]]:
    accepted = [row for row in results if row["resolution_result"] in {
        "exact_accepted", "synonym_resolved",
    }]
    plants: dict[str, tuple] = {}
    traits: dict[tuple[str, str], str] = {}
    for row in accepted:
        scientific_name = str(row["accepted_name"])
        candidate = (scientific_name, row["common_name"], row["native_status"])
        existing = plants.get(scientific_name)
        if existing and existing != candidate:
            raise ValueError(f"conflicting VicFlora metadata for {scientific_name}")
        plants[scientific_name] = candidate
        for trait_name, report_field in CONTROLLED_TRAITS.items():
            value = str(row.get(report_field) or "")
            if value:
                traits[(scientific_name, trait_name)] = value
    return list(plants.values()), [
        (scientific_name, trait_name, value)
        for (scientific_name, trait_name), value in traits.items()
    ]


def load_database(
    config: DatabaseConfig,
    source_id: int,
    results: list[dict],
) -> tuple[int, int]:
    plants, traits = rows_for_database(results)
    if not plants:
        return 0, 0
    controlled = ",".join(sorted(CONTROLLED_TRAITS))
    sql = rf"""
BEGIN;
CREATE TEMP TABLE plant_stage (
    scientific_name text PRIMARY KEY, common_name text, native_status text
) ON COMMIT DROP;
\copy plant_stage FROM STDIN WITH (FORMAT csv)
{_copy_csv(plants)}\.
CREATE TEMP TABLE trait_stage (
    scientific_name text NOT NULL, trait_name text NOT NULL, trait_value text NOT NULL,
    PRIMARY KEY (scientific_name, trait_name)
) ON COMMIT DROP;
\copy trait_stage FROM STDIN WITH (FORMAT csv)
{_copy_csv(traits)}\.
INSERT INTO plant_species (scientific_name, common_name, native_status)
SELECT scientific_name, NULLIF(common_name, ''), NULLIF(native_status, '')
FROM plant_stage
ON CONFLICT (scientific_name) DO UPDATE SET
    common_name = COALESCE(EXCLUDED.common_name, plant_species.common_name),
    native_status = COALESCE(EXCLUDED.native_status, plant_species.native_status);
DELETE FROM plant_trait t
USING plant_species p, plant_stage s
WHERE t.plant_species_id = p.plant_species_id
  AND p.scientific_name = s.scientific_name
  AND t.source_id = :'source_id'
  AND t.trait_name = ANY(string_to_array(:'controlled_traits', ','));
INSERT INTO plant_trait (plant_species_id, source_id, trait_name, trait_value)
SELECT p.plant_species_id, :'source_id', s.trait_name, s.trait_value
FROM trait_stage s
JOIN plant_species p USING (scientific_name);
COMMIT;
"""
    run_psql(
        config,
        sql,
        variables={"source_id": source_id, "controlled_traits": controlled},
    )
    return len(plants), len(traits)


def run(args: argparse.Namespace) -> tuple[list[dict], int, int]:
    inputs = read_name_list(args.input)
    unique_queries = list(dict.fromkeys(
        item["query_name"] for item in inputs if not item["duplicate"]
    ))
    responses = load_cache(
        args.cache, unique_queries, refresh=args.refresh, offline=args.offline,
        batch_size=args.batch_size,
    )
    results = resolve_rows(inputs, responses)
    write_report(args.report, results)

    config = DatabaseConfig.from_environment()
    source_id = register_source(config, SOURCE)
    load_id = start_data_load(
        config, source_id,
        f"VicFlora exact-name resolution from reviewed list {args.input.name}; "
        f"mapping report {args.report}",
    )
    accepted_inputs = sum(row["resolution_result"] in {
        "exact_accepted", "synonym_resolved",
    } for row in results)
    try:
        species_count, trait_count = load_database(config, source_id, results)
        summary = Counter(str(row["resolution_result"]) for row in results)
        finish_data_load(
            config,
            load_id,
            status="complete",
            received=len(inputs),
            accepted=accepted_inputs,
            rejected=len(inputs) - accepted_inputs,
            notes=(
                f"resolution_counts={dict(sorted(summary.items()))}; "
                f"unique_species_loaded={species_count}; trait_rows_loaded={trait_count}; "
                "exact-name matching only; no fuzzy matching; no local-suitability inference"
            ),
        )
    except Exception as exc:
        finish_data_load(
            config, load_id, status="failed", received=len(inputs), accepted=None,
            rejected=None, notes=f"VicFlora load failed: {exc}",
        )
        raise
    return results, species_count, trait_count


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, required=True,
        help="UTF-8 file: original_name with optional tab-separated reviewed query_name",
    )
    parser.add_argument(
        "--cache", type=Path,
        default=Path.home() / ".cache/regrove/vicflora/taxon-names.json",
    )
    parser.add_argument(
        "--report", type=Path,
        default=Path.home() / ".cache/regrove/vicflora/resolution-report.csv",
    )
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)
    try:
        results, species_count, trait_count = run(args)
    except Exception as exc:
        LOG.error("VicFlora plant load failed: %s", exc)
        return 1
    counts = Counter(str(row["resolution_result"]) for row in results)
    LOG.info("Resolution counts: %s", dict(sorted(counts.items())))
    LOG.info("Loaded %s unique species and %s source-backed trait rows", species_count, trait_count)
    LOG.info("Resolution report: %s", args.report)
    for row in results:
        if row["resolution_result"] not in {"exact_accepted", "synonym_resolved"}:
            LOG.warning("%s: %s (%s)", row["original_name"], row["resolution_result"], row["notes"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
