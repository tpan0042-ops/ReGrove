#orchestrates the retrieval and comparison of ecological context data for a given postcode, including EVC records and species evidence, and returns a structured result indicating whether the postcode is supported and the comparison findings.
from queries.local_context import fetch_evc, fetch_species_evidence
from queries.postcode_exists import postcode_exists  
from context.compare import compare_context


def get_area_comparison(postcode: str) -> dict:
    if not postcode_exists(postcode):
        return {"supported": False, "postcode": postcode}

    historical_evc = fetch_evc(postcode, 1750)
    current_evc = fetch_evc(postcode, 2005)
    species_evidence = fetch_species_evidence(postcode)

    result = compare_context(postcode, historical_evc, current_evc, species_evidence)
    result["supported"] = True
    return result