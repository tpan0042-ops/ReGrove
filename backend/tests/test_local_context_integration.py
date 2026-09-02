from queries.local_context import fetch_evc, fetch_species_evidence
from context.compare import compare_context

# Replace with a postcode confirmed present in regrove_demo:
#   SELECT DISTINCT postcode FROM postcode_evc_context;
TEST_POSTCODE = "3170"

# Replace with a postcode confirmed to have little/no data in regrove_demo,
# for AC1.2.3's sparse-data requirement:
#3053 only has 4 records in postcode_evc_context
SPARSE_TEST_POSTCODE = "3053"


def test_fetch_evc_returns_rows_for_known_postcode():
    historical = fetch_evc(TEST_POSTCODE, 1750)
    current = fetch_evc(TEST_POSTCODE, 2005)
    assert historical or current


def test_fetch_species_evidence_returns_expected_shape():
    evidence = fetch_species_evidence(TEST_POSTCODE)
    if evidence:
        row = evidence[0]
        assert "scientific_name" in row
        assert "record_count" in row
        assert "earliest_record_date" in row
        assert "latest_record_date" in row


def test_compare_context_runs_end_to_end_against_real_data():
    historical_evc = fetch_evc(TEST_POSTCODE, 1750)
    current_evc = fetch_evc(TEST_POSTCODE, 2005)
    species_evidence = fetch_species_evidence(TEST_POSTCODE)

    result = compare_context(TEST_POSTCODE, historical_evc, current_evc, species_evidence)

    assert result["postcode"] == TEST_POSTCODE
    assert len(result["historical_species"]) <= 5
    assert len(result["current_species"]) <= 5
    assert len(result["continuous_species"]) <= 5


def test_sparse_data_postcode_does_not_crash():
    historical_evc = fetch_evc(SPARSE_TEST_POSTCODE, 1750)
    current_evc = fetch_evc(SPARSE_TEST_POSTCODE, 2005)
    species_evidence = fetch_species_evidence(SPARSE_TEST_POSTCODE)
    result = compare_context(SPARSE_TEST_POSTCODE, historical_evc, current_evc, species_evidence)
    assert len(result["historical_species"]) <= 5
    assert len(result["current_species"]) <= 5