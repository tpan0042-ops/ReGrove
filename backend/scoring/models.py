from dataclasses import dataclass

@dataclass
#class to represent a plant candidate for scoring
class Candidate:
    plant_species_id: int
    common_name: str
    evidence_source_count: int
    suitability_status: str
    traits: dict[str, list[str]]   

@dataclass
#to store user's backyard context for scoring
class UserContext:
    property_size: str        #from survey
    gaps: set[int]            #habitat_requirement_ids

@dataclass
#to store a scored candidate with reasons for the score
class ScoredCandidate:
    candidate: Candidate
    score: float
    reasons: list[str]         #human-readable, for the "why recommended" UI