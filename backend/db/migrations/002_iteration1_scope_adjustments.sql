BEGIN;

ALTER TABLE fauna_occurrence_summary
    ADD COLUMN period_start date,
    ADD COLUMN period_end date,
    ADD CONSTRAINT fauna_occurrence_summary_period_check
        CHECK (period_end IS NULL OR period_start IS NULL OR period_end >= period_start),
    DROP CONSTRAINT fauna_occurrence_summary_postcode_fauna_species_id_source_i_key,
    ADD CONSTRAINT fauna_occurrence_summary_window_uq
        UNIQUE NULLS NOT DISTINCT (
            postcode, fauna_species_id, source_id, period_start, period_end
        );

ALTER TABLE fauna_garden_relevance
    ADD COLUMN reviewed_at timestamptz,
    ADD COLUMN rule_version text;

-- One evidence source has one current rule for a guild/requirement pair.
-- Status and evidence describe that row and are updated rather than duplicated.
ALTER TABLE guild_habitat_rule
    ADD CONSTRAINT guild_habitat_rule_relationship_source_uq
        UNIQUE (fauna_guild_id, habitat_requirement_id, source_id);

-- One evidence source has one current plant/resource assertion.
ALTER TABLE plant_resource_evidence
    ADD CONSTRAINT plant_resource_evidence_relationship_source_uq
        UNIQUE (plant_species_id, habitat_requirement_id, source_id);

-- One evidence source has one current suitability conclusion per plant/bioregion.
ALTER TABLE local_plant_suitability
    ADD CONSTRAINT local_plant_suitability_relationship_source_uq
        UNIQUE (plant_species_id, bioregion_id, source_id);

COMMIT;
