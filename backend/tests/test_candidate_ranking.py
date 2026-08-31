from db.queries.candidates import fetch_candidates
from scoring.mapping import rows_to_candidates
from scoring.models import UserContext
from scoring.rank import rank_candidates

def test_sample_data_returns_expected_plants():
    # Postcode 3233 and habitat_requirement ids 1, 2 correspond to the
    # SAMPLE bioregion / SAMPLE dense refuge / SAMPLE nectar resource rows
    # in 001_sample_data.sql — check actual ids via:
    #   SELECT habitat_requirement_id, requirement_name FROM habitat_requirement;
    rows = fetch_candidates(postcode="3233", habitat_requirement_ids=[1, 2])
    candidates = rows_to_candidates(rows)

    names = {c.common_name for c in candidates}
    assert "SAMPLE dense shrub" in names
    assert "SAMPLE nectar shrub" in names

    user = UserContext(property_size="medium", gaps={1, 2})
    ranked = rank_candidates(candidates, user)
    assert len(ranked) == 2