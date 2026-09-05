from dataclasses import dataclass
from datetime import date

#class to hold EVC record information
@dataclass
class EvcRecord:
    evc_code: str
    evc_name: str
    conservation_status: str | None
    overlap_percent: float

#class to hold vba species record information for both flora and fauna
@dataclass
class SpeciesEvidence:
    scientific_name: str
    common_name: str | None
    category: str | None       #fauna - taxon_group; flora - native_status
    kind: str                   #"fauna" or "flora"
    record_count: int
    earliest_record_date: date | None
    latest_record_date: date | None
    classification: str = "unknown"
    confidence: str = "Low"

#class to hold the comparison result for a given postcode
@dataclass
class ComparisonResult:
    postcode: str
    vegetation_lost: list[EvcRecord]
    vegetation_retained: list[EvcRecord]
    historical_species: list[SpeciesEvidence]
    current_species: list[SpeciesEvidence]
    spans_cutoff_species: list[SpeciesEvidence]
    limitation_note: str