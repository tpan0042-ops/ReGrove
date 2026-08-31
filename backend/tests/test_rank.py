from scoring.models import Candidate, UserContext
from scoring.rank import score_candidate

def test_more_evidence_scores_higher():
    weak = Candidate(1, "Plant A", evidence_source_count=1, suitability_status="sample_candidate", traits={})
    strong = Candidate(2, "Plant B", evidence_source_count=3, suitability_status="sample_candidate", traits={})
    user = UserContext(property_size="medium", gaps=set())

    assert score_candidate(strong, user).score > score_candidate(weak, user).score

def test_size_mismatch_penalised_with_reason():
    candidate = Candidate(1, "Big Tree", evidence_source_count=1,
                           suitability_status="sample_candidate", traits={"mature_size": "large"})
    user = UserContext(property_size="small", gaps=set())

    result = score_candidate(candidate, user)
    assert any("small property" in r for r in result.reasons)