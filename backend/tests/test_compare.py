from datetime import date
from context.classify import classify_species
from context.compare import build_evc_comparison, rank_species, compare_context


def test_classify_spans_cutoff():
    assert classify_species(date(1950, 1, 1), date(2020, 1, 1)) == "spans_cutoff"


def test_classify_historical_only():
    assert classify_species(date(1950, 1, 1), date(1995, 1, 1)) == "historical_only"


def test_classify_current_only():
    assert classify_species(date(2010, 1, 1), date(2020, 1, 1)) == "current_only"


def test_classify_exact_cutoff_counts_as_current():
    assert classify_species(date(2000, 1, 1), date(2000, 1, 1)) == "current_only"


def test_classify_spans_cutoff_boundary():
    assert classify_species(date(1999, 12, 31), date(2000, 1, 1)) == "spans_cutoff"


def test_classify_missing_dates_unknown():
    assert classify_species(None, date(2020, 1, 1)) == "unknown"
    assert classify_species(date(1950, 1, 1), None) == "unknown"
