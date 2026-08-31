#for now this fetches from the sample data, but this will be modified to fetch from the real database once the retrieval code is implemented. the tests will be updated accordingly.
from db.connection import get_connection

def fetch_candidates(postcode: str, habitat_requirement_ids: list[int]) -> list[dict]:
    """Returns raw candidate plant rows for a postcode's bioregion(s)
    and a set of habitat_requirement gaps. No scoring happens here —
    just retrieval of everything structurally eligible."""

    sql = """
        SELECT
            ps.plant_species_id,
            ps.common_name,
            ps.native_status,
            lps.suitability_status,
            COUNT(DISTINCT pre.source_id) AS evidence_source_count
        FROM plant_species ps
        JOIN plant_resource_evidence pre
            ON pre.plant_species_id = ps.plant_species_id
        JOIN local_plant_suitability lps
            ON lps.plant_species_id = ps.plant_species_id
        JOIN postcode_bioregion pb
            ON pb.bioregion_id = lps.bioregion_id
        WHERE pb.postcode = %s
          AND pre.habitat_requirement_id = ANY(%s)
        GROUP BY ps.plant_species_id, ps.common_name, ps.native_status, lps.suitability_status
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (postcode, habitat_requirement_ids))
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]

    #attach traits separately — EAV shape means one row per trait value, so this needs its own query and grouping rather than a single join.
    plant_ids = [r["plant_species_id"] for r in rows]
    traits_by_plant = _fetch_traits(plant_ids)
    for row in rows:
        row["traits"] = traits_by_plant.get(row["plant_species_id"], {})

    return rows


def _fetch_traits(plant_ids: list[int]) -> dict[int, dict[str, list[str]]]:
    if not plant_ids:
        return {}

    sql = """
        SELECT plant_species_id, trait_name, trait_value
        FROM plant_trait
        WHERE plant_species_id = ANY(%s)
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (plant_ids,))
            rows = cur.fetchall()

    traits: dict[int, dict[str, list[str]]] = {}
    for plant_id, trait_name, trait_value in rows:
        traits.setdefault(plant_id, {}).setdefault(trait_name, []).append(trait_value)
    return traits