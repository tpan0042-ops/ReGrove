from .weights import EVIDENCE_WEIGHT, SUITABILITY_WEIGHTS, SIZE_MISMATCH_PENALTY
from .models import Candidate, UserContext, ScoredCandidate

#create scoring function that takes a candidate and user context and returns a score and reasons
def score_candidate(candidate: Candidate, user: UserContext) -> ScoredCandidate:
    score = 0.0
    reasons = []

    #score based on evidence source count, with more weight given to plant candidates with more evidence
    score += candidate.evidence_source_count * EVIDENCE_WEIGHT
    if candidate.evidence_source_count > 1:
        reasons.append(f"Supported by {candidate.evidence_source_count} independent sources")

    #score based on suitability status, with more weight given to plant candidates that are more suitable for the user's outdoor space
    score += SUITABILITY_WEIGHTS.get(candidate.suitability_status, 0)

    #penalise plants that are too large for the user's property size, with a reason provided
    mature_size = candidate.traits.get("mature_size")
    if user.property_size == "small" and mature_size == "large":
        score -= SIZE_MISMATCH_PENALTY
        reasons.append("Caution: mature size may not suit a small property")

    return ScoredCandidate(candidate=candidate, score=score, reasons=reasons)


def rank_candidates(candidates: list[Candidate], user: UserContext) -> list[ScoredCandidate]:
    scored = [score_candidate(c, user) for c in candidates]
    #sort scored plant candidates by score in descending order
    return sorted(scored, key=lambda s: s.score, reverse=True)