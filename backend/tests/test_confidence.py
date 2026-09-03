from datetime import date
from context.confidence import classify_confidence


def test_high_confidence_plentiful_and_current():
    assert classify_confidence(50, date(2020, 1, 1), date(2024, 1, 1)) == "High"


def test_low_confidence_sparse_and_historical():
    assert classify_confidence(1, date(1877, 12, 31), date(1877, 12, 31)) == "Low"


def test_plentiful_but_historical_is_not_high():
    assert classify_confidence(500, date(1950, 1, 1), date(1999, 1, 1)) == "Low"


def test_current_but_sparse_is_not_high():
    assert classify_confidence(1, date(2020, 1, 1), date(2024, 1, 1)) == "Low"


def test_medium_confidence_from_spans_cutoff():
    assert classify_confidence(10, date(1995, 1, 1), date(2010, 1, 1)) == "Medium"


def test_spans_cutoff_with_high_count_capped_at_medium():
    assert classify_confidence(500, date(1995, 1, 1), date(2010, 1, 1)) == "Medium"


def test_missing_dates_treated_as_low_recency():
    assert classify_confidence(100, None, None) == "Low"


def test_missing_one_date_treated_as_low_recency():
    assert classify_confidence(100, date(2010, 1, 1), None) == "Low"


def test_negative_record_count_raises():
    try:
        classify_confidence(-1, date(2024, 1, 1), date(2024, 1, 1))
        assert False, "expected ValueError"
    except ValueError:
        pass
