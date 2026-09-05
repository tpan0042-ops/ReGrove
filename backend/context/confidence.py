from datetime import date
from context.classify import classify_species

# Record-count thresholds (proposal — pending team review, see epic DoD #2)
LOW_COUNT_MAX = 4
MEDIUM_COUNT_MAX = 19

_LEVELS = {"Low": 0, "Medium": 1, "High": 2}

_RECENCY_FROM_PERIOD = {
    "current_only": "High",
    "spans_cutoff": "Medium",
    "historical_only": "Low",
    "unknown": "Low",
}


def _count_tier(record_count: int) -> str:
    if record_count <= LOW_COUNT_MAX:
        return "Low"
    if record_count <= MEDIUM_COUNT_MAX:
        return "Medium"
    return "High"


def _recency_tier(earliest_record_date: date | None, latest_record_date: date | None) -> str:
    period = classify_species(earliest_record_date, latest_record_date)
    return _RECENCY_FROM_PERIOD[period]


def classify_confidence(
    record_count: int,
    earliest_record_date: date | None,
    latest_record_date: date | None,
) -> str:
    if record_count < 0:
        raise ValueError("record_count cannot be negative")

    count_tier = _count_tier(record_count)
    recency_tier = _recency_tier(earliest_record_date, latest_record_date)

    weaker = min(count_tier, recency_tier, key=lambda tier: _LEVELS[tier])
    return weaker
