from datetime import date
from context.confidence import classify_confidence


def test_high_confidence_plentiful_and_recent():
    assert classify_confidence(50, date(2024, 1, 1), today=date(2026, 9, 1)) == "High"


def test_low_confidence_sparse_and_old():
    assert classify_confidence(1, date(1877, 12, 31), today=date(2026, 9, 1)) == "Low"


def test_plentiful_but_old_is_not_high():
    # Real case: Maccullochella peelii, 16073 records but earliest in 1760.
    # latest_record_date is recent (2025), so this one IS high recency —
    # this test instead checks the case where a big count is undercut by
    # an old *latest* record.
    assert classify_confidence(500, date(1980, 1, 1), today=date(2026, 9, 1)) == "Low"


def test_recent_but_sparse_is_not_high():
    assert classify_confidence(1, date(2025, 1, 1), today=date(2026, 9, 1)) == "Low"


def test_medium_confidence():
    assert classify_confidence(10, date(2020, 1, 1), today=date(2026, 9, 1)) == "Medium"


def test_missing_date_treated_as_low_recency():
    assert classify_confidence(100, None) == "Low"


def test_negative_record_count_raises():
    try:
        classify_confidence(-1, date(2024, 1, 1))
        assert False, "expected ValueError"
    except ValueError:
        pass