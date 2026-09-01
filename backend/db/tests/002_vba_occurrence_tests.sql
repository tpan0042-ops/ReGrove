\set ON_ERROR_STOP on

BEGIN;

DO $$
DECLARE
    sample_source_id bigint;
    sample_plant_id bigint;
BEGIN
    IF to_regclass('public.plant_occurrence_summary') IS NULL THEN
        RAISE EXCEPTION 'Migration 003 plant_occurrence_summary table is missing';
    END IF;

    SELECT source_id INTO STRICT sample_source_id FROM source ORDER BY source_id LIMIT 1;
    SELECT plant_species_id INTO STRICT sample_plant_id
    FROM plant_species ORDER BY plant_species_id LIMIT 1;

    INSERT INTO plant_occurrence_summary (
        postcode, plant_species_id, source_id, source_taxon_id, record_count,
        latest_record_date, period_start, period_end
    ) VALUES (
        '3233', sample_plant_id, sample_source_id, 'VBA-test-1', 4,
        DATE '2024-12-31', DATE '2020-01-01', DATE '2024-12-31'
    );

    BEGIN
        INSERT INTO plant_occurrence_summary (
            postcode, plant_species_id, source_id, source_taxon_id, record_count,
            latest_record_date, period_start, period_end
        ) VALUES (
            '3233', sample_plant_id, sample_source_id, 'VBA-test-1', 4,
            DATE '2024-12-31', DATE '2020-01-01', DATE '2024-12-31'
        );
        RAISE EXCEPTION 'duplicate plant occurrence window was accepted';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;

    BEGIN
        INSERT INTO plant_occurrence_summary (
            postcode, plant_species_id, source_id, source_taxon_id, record_count,
            period_start, period_end
        ) VALUES (
            '3233', sample_plant_id, sample_source_id, 'VBA-test-2', 1,
            DATE '2024-01-02', DATE '2024-01-01'
        );
        RAISE EXCEPTION 'reversed plant occurrence dates were accepted';
    EXCEPTION WHEN check_violation THEN NULL;
    END;
END $$;

ROLLBACK;

SELECT 'All VBA occurrence migration tests passed.' AS result;
