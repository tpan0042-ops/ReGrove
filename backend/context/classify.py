from datetime import date

CUTOFF = date(2000, 1, 1)


def classify_species(earliest: date | None, latest: date | None) -> str:
    """Classify a species' occurrence evidence relative to a single cutoff.

    A species with evidence entirely before the cutoff is historical_only;
    entirely on/after the cutoff is current_only; records on both sides of the
    cutoff are spans_cutoff. Species missing either date can't be responsibly placed
    and are returned as 'unknown'.
    """
    if earliest is None or latest is None:
        return "unknown"

    is_historical = earliest < CUTOFF
    is_current = latest >= CUTOFF

    if is_historical and is_current:
        return "spans_cutoff"
    if is_historical:
        return "historical_only"
    return "current_only"