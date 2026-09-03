from datetime import date

# Record-count thresholds (proposal — pending team review, see epic DoD #2)
LOW_COUNT_MAX = 4
MEDIUM_COUNT_MAX = 19

# Recency thresholds, in years from today
RECENT_YEARS = 5
MODERATE_YEARS = 15

_LEVELS = {"Low": 0, "Medium": 1, "High": 2}


def _count_tier(record_count: int) -> str:
    if record_count <= LOW_COUNT_MAX:
        return "Low"
    if record_count <= MEDIUM_COUNT_MAX:
        return "Medium"
    return "High"


def _recency_tier(latest_record_date: date | None, today: date | None = None) -> str:
    if latest_record_date is None:
        return "Low"
    today = today or date.today()
    years_since = (today - latest_record_date).days / 365.25
    if years_since <= RECENT_YEARS:
        return "High"
    if years_since <= MODERATE_YEARS:
        return "Medium"
    return "Low"


def classify_confidence(
    record_count: int,
    latest_record_date: date | None,
    today: date | None = None,
) -> str:
    """Classify data confidence from record volume and recency.

    Confidence reflects how much weight a user should give this evidence,
    not species abundance or presence/absence. A species with many old
    records or few recent ones is not treated as High confidence: the
    weaker of the two signals determines the result, since both plentiful
    and recent evidence are required for a strong confidence signal.

    Thresholds are a documented starting proposal (see epic DoD:
    "Threshold value ... documented and agreed with the team") and are
    not yet team-approved; they are isolated here so they can be tuned
    without touching call sites.
    """
    if record_count < 0:
        raise ValueError("record_count cannot be negative")

    count_tier = _count_tier(record_count)
    recency_tier = _recency_tier(latest_record_date, today)

    weaker = min(count_tier, recency_tier, key=lambda tier: _LEVELS[tier])
    return weaker