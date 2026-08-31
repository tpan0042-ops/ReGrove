from .models import Candidate

#map retrieved database rows to Candidate dataclass instances
def rows_to_candidates(rows: list[dict]) -> list[Candidate]:
    return [
        Candidate(
            plant_species_id=r["plant_species_id"],
            common_name=r["common_name"],
            evidence_source_count=r["evidence_source_count"],
            suitability_status=r["suitability_status"],
            traits=r["traits"],
        )
        for r in rows
    ]