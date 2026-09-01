\set ON_ERROR_STOP on

BEGIN;

DO $$
DECLARE
    expected_tables text[] := ARRAY[
        'source', 'data_load', 'postcode', 'bioregion', 'postcode_bioregion',
        'evc_class', 'postcode_evc_context', 'fauna_species',
        'fauna_occurrence_summary', 'fauna_trait', 'fauna_guild',
        'fauna_guild_membership', 'fauna_garden_relevance',
        'habitat_requirement', 'guild_habitat_rule', 'plant_species',
        'plant_trait', 'plant_resource_evidence', 'local_plant_suitability'
    ];
    actual_count integer;
BEGIN
    SELECT count(*) INTO actual_count
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = ANY(expected_tables);

    IF actual_count <> cardinality(expected_tables) THEN
        RAISE EXCEPTION 'Expected % ReGrove tables, found %', cardinality(expected_tables), actual_count;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') THEN
        RAISE EXCEPTION 'PostGIS extension is not enabled';
    END IF;

    SELECT count(*) INTO actual_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND (
          (table_name = 'fauna_occurrence_summary' AND column_name IN ('period_start', 'period_end'))
          OR (table_name = 'fauna_garden_relevance' AND column_name IN ('reviewed_at', 'rule_version'))
      );
    IF actual_count <> 4 THEN
        RAISE EXCEPTION 'Iteration 1 adjustment columns are incomplete';
    END IF;
END $$;

DO $$
BEGIN
    BEGIN
        INSERT INTO data_load (source_id, status) VALUES (-1, 'must_fail');
        RAISE EXCEPTION 'Invalid foreign key insertion unexpectedly succeeded';
    EXCEPTION WHEN foreign_key_violation THEN
        NULL;
    END;
END $$;

DO $$
DECLARE
    sample_occurrence fauna_occurrence_summary%ROWTYPE;
BEGIN
    SELECT o.* INTO STRICT sample_occurrence
    FROM fauna_occurrence_summary o
    JOIN fauna_species f USING (fauna_species_id)
    WHERE f.scientific_name = 'SAMPLE fauna alpha';

    BEGIN
        INSERT INTO fauna_occurrence_summary (
            postcode, fauna_species_id, source_id, record_count,
            latest_record_date, period_start, period_end
        ) VALUES (
            sample_occurrence.postcode, sample_occurrence.fauna_species_id,
            sample_occurrence.source_id, 1, DATE '2026-01-01',
            DATE '2026-01-02', DATE '2026-01-01'
        );
        RAISE EXCEPTION 'An occurrence window ending before it starts was accepted';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;

    INSERT INTO fauna_occurrence_summary (
        postcode, fauna_species_id, source_id, record_count,
        latest_record_date, period_start, period_end
    ) VALUES (
        sample_occurrence.postcode, sample_occurrence.fauna_species_id,
        sample_occurrence.source_id, 1, DATE '2024-12-31',
        DATE '2024-01-01', DATE '2024-12-31'
    );

    BEGIN
        INSERT INTO fauna_occurrence_summary (
            postcode, fauna_species_id, source_id, record_count,
            latest_record_date, period_start, period_end
        ) VALUES (
            sample_occurrence.postcode, sample_occurrence.fauna_species_id,
            sample_occurrence.source_id, 1, DATE '2024-12-31',
            DATE '2024-01-01', DATE '2024-12-31'
        );
        RAISE EXCEPTION 'An identical occurrence summary window was accepted twice';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
END $$;

DO $$
DECLARE
    sample_bioregion_id bigint;
BEGIN
    SELECT bioregion_id INTO STRICT sample_bioregion_id
    FROM bioregion WHERE bioregion_name = 'SAMPLE bioregion';

    BEGIN
        INSERT INTO postcode_bioregion (postcode, bioregion_id, overlap_percent)
        VALUES ('3233', sample_bioregion_id, 100);
        RAISE EXCEPTION 'POSTCODE_BIOREGION composite primary key did not reject a duplicate';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
END $$;

DO $$
DECLARE
    rule_row guild_habitat_rule%ROWTYPE;
    resource_row plant_resource_evidence%ROWTYPE;
    suitability_row local_plant_suitability%ROWTYPE;
BEGIN
    SELECT * INTO STRICT rule_row FROM guild_habitat_rule LIMIT 1;
    BEGIN
        INSERT INTO guild_habitat_rule (
            fauna_guild_id, habitat_requirement_id, source_id, status, evidence
        ) VALUES (
            rule_row.fauna_guild_id, rule_row.habitat_requirement_id,
            rule_row.source_id, 'conditional', 'duplicate must fail'
        );
        RAISE EXCEPTION 'Duplicate guild-habitat-source relationship was accepted';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;

    SELECT * INTO STRICT resource_row FROM plant_resource_evidence LIMIT 1;
    BEGIN
        INSERT INTO plant_resource_evidence (
            plant_species_id, habitat_requirement_id, source_id, evidence_summary
        ) VALUES (
            resource_row.plant_species_id, resource_row.habitat_requirement_id,
            resource_row.source_id, 'duplicate must fail'
        );
        RAISE EXCEPTION 'Duplicate plant-resource-source relationship was accepted';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;

    SELECT * INTO STRICT suitability_row FROM local_plant_suitability LIMIT 1;
    BEGIN
        INSERT INTO local_plant_suitability (
            plant_species_id, bioregion_id, source_id, suitability_status, evidence_summary
        ) VALUES (
            suitability_row.plant_species_id, suitability_row.bioregion_id,
            suitability_row.source_id, 'duplicate', 'duplicate must fail'
        );
        RAISE EXCEPTION 'Duplicate plant-bioregion-source relationship was accepted';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
END $$;

DO $$
DECLARE
    sample_fauna_id bigint;
    sample_guild_id bigint;
BEGIN
    SELECT fauna_species_id INTO STRICT sample_fauna_id
    FROM fauna_species WHERE scientific_name = 'SAMPLE fauna alpha';
    SELECT fauna_guild_id INTO STRICT sample_guild_id
    FROM fauna_guild WHERE guild_name = 'SAMPLE small insectivorous birds';

    BEGIN
        INSERT INTO fauna_guild_membership (fauna_species_id, fauna_guild_id, membership_role)
        VALUES (sample_fauna_id, sample_guild_id, 'primary');
        RAISE EXCEPTION 'FAUNA_GUILD_MEMBERSHIP composite primary key did not reject a duplicate';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;
END $$;

DO $$
DECLARE
    n integer;
BEGIN
    SELECT count(*) INTO n
    FROM fauna_guild_membership m
    JOIN fauna_species f USING (fauna_species_id)
    WHERE f.scientific_name = 'SAMPLE fauna alpha';
    IF n < 2 THEN
        RAISE EXCEPTION 'One fauna species cannot be retrieved in multiple guilds';
    END IF;

    SELECT count(DISTINCT e.plant_species_id) INTO n
    FROM plant_resource_evidence e
    JOIN habitat_requirement h USING (habitat_requirement_id)
    WHERE h.requirement_name = 'SAMPLE dense refuge';
    IF n < 2 THEN
        RAISE EXCEPTION 'One habitat requirement is not connected to multiple plants';
    END IF;

    SELECT count(*) INTO n
    FROM plant_trait t
    JOIN plant_species p USING (plant_species_id)
    WHERE p.scientific_name = 'SAMPLE plant alpha'
      AND t.trait_name = 'sample_foliage_density';
    IF n < 2 THEN
        RAISE EXCEPTION 'Multiple values for one plant trait name were not preserved';
    END IF;

    SELECT count(*) INTO n
    FROM data_load d
    JOIN source s USING (source_id)
    WHERE s.source_name = 'SAMPLE fauna occurrence';
    IF n < 2 THEN
        RAISE EXCEPTION 'One source does not have multiple DATA_LOAD records';
    END IF;

    SELECT count(*) INTO n
    FROM fauna_garden_relevance r
    JOIN fauna_species f USING (fauna_species_id)
    WHERE f.scientific_name = 'SAMPLE fauna alpha'
      AND r.reviewed_at IS NOT NULL
      AND r.rule_version = 'sample-v1';
    IF n <> 1 THEN
        RAISE EXCEPTION 'Garden-relevance review metadata was not preserved';
    END IF;
END $$;

DO $$
DECLARE
    evc_count integer;
    local_plant_count integer;
BEGIN
    SELECT count(DISTINCT c.evc_id), count(DISTINCT p.plant_species_id)
    INTO evc_count, local_plant_count
    FROM postcode pc
    JOIN postcode_evc_context c ON c.postcode = pc.postcode
    JOIN postcode_bioregion pb ON pb.postcode = pc.postcode
    JOIN local_plant_suitability l ON l.bioregion_id = pb.bioregion_id
    JOIN plant_species p ON p.plant_species_id = l.plant_species_id
    WHERE pc.postcode = '3233';

    IF evc_count <> 1 OR local_plant_count <> 2 THEN
        RAISE EXCEPTION
            'Iteration 1 context query expected 1 EVC and 2 SAMPLE plants; found % and %',
            evc_count, local_plant_count;
    END IF;
END $$;

DO $$
DECLARE
    candidate_count integer;
BEGIN
    SELECT count(DISTINCT p.plant_species_id) INTO candidate_count
    FROM postcode pc
    JOIN fauna_occurrence_summary o ON o.postcode = pc.postcode
    JOIN fauna_garden_relevance gr
      ON gr.fauna_species_id = o.fauna_species_id
     AND gr.relevance_status = 'candidate'
    JOIN fauna_guild_membership gm ON gm.fauna_species_id = o.fauna_species_id
    JOIN guild_habitat_rule r
      ON r.fauna_guild_id = gm.fauna_guild_id
     AND r.status IN ('validated_for_coarse_use', 'conditional')
    JOIN plant_resource_evidence e
      ON e.habitat_requirement_id = r.habitat_requirement_id
    JOIN plant_species p ON p.plant_species_id = e.plant_species_id
    JOIN postcode_bioregion pb ON pb.postcode = pc.postcode
    JOIN local_plant_suitability l
      ON l.bioregion_id = pb.bioregion_id
     AND l.plant_species_id = p.plant_species_id
    WHERE pc.postcode = '3233';

    IF candidate_count <> 2 THEN
        RAISE EXCEPTION 'Main reasoning query expected 2 SAMPLE plants, found %', candidate_count;
    END IF;
END $$;

DO $$
DECLARE
    forbidden_count integer;
BEGIN
    SELECT count(*) INTO forbidden_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND (
          lower(table_name) LIKE '%bioscore%'
          OR lower(table_name) LIKE '%recommendation%'
          OR lower(table_name) IN ('user', 'users', 'user_profile', 'user_profiles', 'candidate_plant')
      );
    IF forbidden_count <> 0 THEN
        RAISE EXCEPTION 'Forbidden BioScore, recommendation, candidate, or user-profile table exists';
    END IF;
END $$;

ROLLBACK;

SELECT 'All ReGrove database schema tests passed.' AS result;
