# ReGrove database v1

This is the first research-backed PostgreSQL/PostGIS schema. It contains only
the 19 approved tables. The schema is intentionally broader than the Iteration
1 application so it can remain fauna-ready without an early redesign.

Iteration 1 operational priority is:

```text
postcode
→ historical vegetation / local ecological context
→ locally appropriate plant candidates
```

Fauna occurrence, trait, guild, habitat-rule and plant-resource tables are
forward-compatible structures for later fauna-informed iterations. They do not
need to be fully populated or exposed through the Iteration 1 API or frontend.
Candidate plants remain derived query/application results, not persisted or
guaranteed recommendations. No BioScore, recommendation, user, or profile table
is persisted.

The included seed file is clearly marked **SAMPLE DATA ONLY**. Occurrence
counts must not be interpreted as abundance, record absence does not prove
species absence, EVC describes historical vegetation-community context rather
than individual historical plant existence or loss, and regional suitability
is not parcel-level suitability. Plant resource evidence must not be presented
as proof that a plant attracts a specific fauna species.

Fauna and plant trait values are intentionally stored as text in v1 so source
values and heterogeneous records can be preserved without silent coercion.
Frequently used traits may be normalised into typed structures in a later,
evidence-led migration.

## Local setup

Docker Compose uses PostgreSQL 16 with PostGIS 3.4 and exposes it on local port
`5433` by default. Override `POSTGRES_DB`, `POSTGRES_USER`,
`POSTGRES_PASSWORD`, or `REGROVE_DB_PORT` in an ignored `.env` file if needed.

```bash
docker compose up -d db
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U regrove -d regrove \
  < backend/db/migrations/001_initial_regrove_schema.sql
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U regrove -d regrove \
  < backend/db/migrations/002_iteration1_scope_adjustments.sql
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U regrove -d regrove \
  < backend/db/seeds/001_sample_data.sql
```

`CREATE EXTENSION postgis` requires a database role permitted to create the
extension. The supplied local container user has that permission. A managed
production database administrator must enable PostGIS before this migration is
applied there.

## Tests

With the migration and sample seed applied:

```bash
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U regrove -d regrove \
  < backend/db/tests/001_schema_tests.sql
```

The test transaction rolls back its own attempted writes. It checks schema and
PostGIS creation, foreign keys, both composite primary keys, observation-window
validation and uniqueness, duplicate prevention for evidence relationships,
review metadata, multi-label fauna guilds, repeated plant trait values,
multiple data loads per source, the Iteration 1 context/local-plant query, the
later fauna reasoning query, and the absence of
BioScore/recommendation/user-profile tables.

## Duplicate prevention

- `guild_habitat_rule` is unique by guild, habitat requirement, and source. A
  source has one current rule for that relationship; status/evidence are
  updated on that row.
- `plant_resource_evidence` is unique by plant, habitat requirement, and
  source. Multiple sources may independently support the same relationship.
- `local_plant_suitability` is unique by plant, bioregion, and source. Multiple
  sources may independently record a regional suitability conclusion.

These constraints intentionally exclude descriptive status/evidence fields so
editing a conclusion does not create a duplicate relationship.

## Migration policy

The repository had no ORM or migration framework when this schema was added.
Numbered native SQL keeps the first database version reviewable without adding
an unused ORM stack. Apply each migration exactly once, in filename order.

Migration `002` does not silently remove pre-existing duplicates. If a database
already contains duplicate guild rules, plant-resource evidence, or local
suitability rows for the same relationship/source keys, the migration will stop
when adding the unique constraint. Those records must be reviewed and merged
with provenance preserved before retrying.

The observation-window constraint uses PostgreSQL's `UNIQUE NULLS NOT
DISTINCT`, which requires PostgreSQL 15 or later. The supplied Compose service
uses PostgreSQL 16.

Foreign keys use PostgreSQL's default `NO ACTION` deletion behaviour. No
cascade deletes are introduced because provenance-bearing evidence should not
be removed implicitly.
