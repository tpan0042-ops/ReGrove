from context.classify import classify_species
from context.confidence import classify_confidence


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


def rank_species(
    species_list: list[dict], classification_filter: set[str], limit: int = 5) -> list[dict]:
    matching = [s for s in species_list if s["classification"] in classification_filter]
    return sorted(matching, key=lambda s: s["record_count"], reverse=True)[:limit]


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
        species["confidence"] = classify_confidence(
            species.get("record_count", 0),
            species.get("earliest_record_date"),
            species.get("latest_record_date"),
        )

    vegetation_lost, vegetation_retained = build_evc_comparison(historical_evc, current_evc)

    return {
        "postcode": postcode,
        "vegetation_lost": vegetation_lost,
        "vegetation_retained": vegetation_retained,
        "historical_species": rank_species(species_evidence, {"historical_only"}),
        "current_species": rank_species(species_evidence, {"current_only"}),
        "spans_cutoff_species": rank_species(species_evidence, {"spans_cutoff"}),
        "limitation_note": (
            "Occurrence and vegetation records show what has been documented, not confirmed presence or absence. Species without both an earliest and latest record date cannot be classified as historical, current, or spanning the cutoff."
        ),
    }
