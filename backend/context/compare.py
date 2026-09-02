from datetime import date

CUTOFF = date(2000, 1, 1)

"""Classify a species' occurrence evidence relative to a single cutoff.

    A species with evidence entirely before the cutoff is historical_only;
    entirely on/after the cutoff is current_only; spanning the cutoff is
    continuous. Species missing either date can't be responsibly placed
    and are returned as 'unknown'.
    """
def classify_species(earliest: date | None, latest: date | None) -> str:

    if earliest is None or latest is None:
        return "unknown"

    is_historical = earliest < CUTOFF
    is_current = latest >= CUTOFF

    if is_historical and is_current:
        return "spans_cutoff"
    if is_historical:
        return "historical_only"
    return "current_only"

#compare historical and current EVC records to determine which have been lost or retained
def build_evc_comparison(
    historical_evc: list[dict], current_evc: list[dict]
) -> tuple[list[dict], list[dict]]:
    historical_codes = {row["evc_code"] for row in historical_evc}
    current_codes = {row["evc_code"] for row in current_evc}

    lost_codes = historical_codes - current_codes
    retained_codes = historical_codes & current_codes

    vegetation_lost = [row for row in historical_evc if row["evc_code"] in lost_codes]
    vegetation_retained = [row for row in historical_evc if row["evc_code"] in retained_codes]
    return vegetation_lost, vegetation_retained

#ranks species by record count and filters by classification, returning the top N species
def rank_species(
    species_list: list[dict], classification_filter: set[str], limit: int = 5
) -> list[dict]:
    matching = [s for s in species_list if s["classification"] in classification_filter]
    return sorted(matching, key=lambda s: s["record_count"], reverse=True)[:limit]

#compares historical and current EVC records and species evidence for a given postcode, returning a structured result with limitations
def compare_context(
    postcode: str,
    historical_evc: list[dict],
    current_evc: list[dict],
    species_evidence: list[dict],
) -> dict:
    for species in species_evidence:
        species["classification"] = classify_species(
            species.get("earliest_record_date"), species.get("latest_record_date")
        )

    vegetation_lost, vegetation_retained = build_evc_comparison(historical_evc, current_evc)

    return {
        "postcode": postcode,
        "vegetation_lost": vegetation_lost,
        "vegetation_retained": vegetation_retained,
        "historical_species": rank_species(species_evidence, {"historical_only"}),
        "current_species": rank_species(species_evidence, {"current_only"}),
        "continuous_species": rank_species(species_evidence, {"spans_cutoff"}),
        "limitation_note": (
            "Occurrence and vegetation records show what has been documented, not confirmed presence or absence. Species without both an earliest and latest record date cannot be classified as historical, current, or continuous."
        ),
    }