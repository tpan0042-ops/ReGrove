# ReGrove real-data ingestion

This directory contains reproducible loaders for reference data. It is separate
from `seeds/001_sample_data.sql`, which contains relationship-test fixtures only
and must never be described as real ecological data.

Iteration 1 data flow is:

```text
postcode
├── Victorian Bioregion
├── EVC 1750 / 2005 context
├── VBA flora 1-minute occurrence evidence
└── VBA fauna 1-minute occurrence evidence
```

Postcode, Victorian EVC, VicFlora taxonomy and local-file VBA ingestion are
implemented. The Victorian Bioregion loader now consumes the downloaded official
VBIOREG100 SHP; the raw package remains local and ignored by Git.
Local plant-suitability evidence remains a separate later stage.

## Postcode source

The loader uses the Australian Bureau of Statistics (ABS) **ASGS Edition 3
(2021) Postal Areas** feature layer:

- Provider: Australian Bureau of Statistics
- Service: <https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/POA/MapServer/0>
- Dataset documentation: <https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/non-abs-structures/postal-areas>
- Access: ArcGIS REST query returning GeoJSON
- Licence: Creative Commons Attribution 4.0 International (CC BY 4.0)
- Source fields: `poa_code_2021`, `poa_name_2021`,
  `area_albers_sqkm`, `asgs_loci_uri_2021`
- Source layer geometry: polygon in Web Mercator (EPSG:3857); the query requests
  GeoJSON transformed by ABS to EPSG:4326
- ReGrove mapping: `poa_code_2021` → `postcode.postcode`; polygon geometry →
  `postcode.geometry`; registered ABS source → `postcode.source_id`

ABS Postal Areas are Mesh Block approximations of postcodes for statistical
use. They are not official Australia Post delivery boundaries. The 2021 layer
has no state field. The loader selects the verified `3xxx` POA set (694 records)
as the Victorian operational subset. Some cross-border postcodes can therefore
retain geometry outside Victoria; geometry is not clipped or silently changed.

The API response is cached at `~/.cache/regrove/` by default, outside the
repository. Do not commit downloaded boundaries.

## Database environment

The loader invokes `psql` and reads standard PostgreSQL variables. Example
values for the supplied local Compose database are:

```text
PGHOST=localhost
PGPORT=5433
PGDATABASE=regrove
PGUSER=regrove
PGPASSWORD=<local password>
PSQL=/optional/path/to/psql
CURL=/optional/path/to/curl
```

`PGPASSWORD` is intentionally not defaulted in source code. Use an ignored
`.env`/shell environment or PostgreSQL `.pgpass`; never commit credentials.
The downloader uses `curl` with normal TLS certificate verification and writes
the cache atomically; it never disables HTTPS verification.

## Run

Apply migrations first, then start the loader from the repository root:

```bash
export PGHOST=localhost PGPORT=5433 PGDATABASE=regrove PGUSER=regrove
export PGPASSWORD='<your local password>'
python3 backend/db/ingestion/postcode/load_postcodes.py
python3 backend/db/ingestion/bioregion/load_bioregions.py \
  --input /absolute/path/to/VBIOREG100.shp
python3 backend/db/ingestion/evc/load_evc.py --postcode 3233 --period both
```

To use an already downloaded ABS GeoJSON response without network access:

```bash
python3 backend/db/ingestion/postcode/load_postcodes.py \
  --input /absolute/path/abs_poa_2021_victoria.geojson
```

The local file must be an EPSG:4326 GeoJSON `FeatureCollection` from the same
ABS query, with polygon geometry and `poa_code_2021`. The loader rejects null,
duplicate, non-`3xxx`, empty, non-polygon, implausible-coordinate, invalid, or
wrong-SRID data. It expects exactly 694 records for this source version.

Each run registers `SOURCE`, creates a `DATA_LOAD` row, reports received,
accepted and rejected counts, and marks the load `complete` or `failed`. The
database write is transactional. Re-running updates the same ABS postcode rows;
it does not create duplicates. A postcode owned by another source is rejected
rather than silently reassigned.

## Victorian Bioregion replacement and relationship derivation

New I1 loads use the official downloadable **Victorian Bioregions — Mapped at
1:100,000 (version 3.0, May 2004)** (`VBIOREG100`):

- Provider: Victorian Department of Energy, Environment and Climate Action
- Dataset: <https://discover.data.vic.gov.au/dataset/victorian-bioregions-mapped-at-1-100000-version-3-0-may2004>
- DataShare metadata identifier: `3508ad58-e66b-50e4-9717-0338845ded77`
- Required access: order/download the official `VBIOREG100 SHP`; no scraper or
  runtime HTML extraction is used
- Licence: Creative Commons Attribution 4.0 International
- Published CRS: GDA94 (EPSG:4283)
- Documented SHP fields used: `BIOREGCODE` and `BIOREGION`
- Expected statewide class count from official metadata: 28. The downloaded SHP
  contains 273 polygon fragments for those 28 code/name regions; fragments are
  validated and dissolved by code/name before postcode intersections.

The local package is present at
`Victorian Bioregions/ll_gda94/esrishape/whole_of_dataset/victoria/FLORAFAUNA1/VBIOREG100.shp`.
Existing national IBRA rows remain as historical/provenance data after the
Victorian replacement load. Current validation filters to the Victorian source
and never mixes the two products. The loader validates required SHP
components and converts the official local file to EPSG:4326 through GDAL
before the PostGIS write.

PostGIS rebuilds `postcode_bioregion` for this source after loading the regions.
Every positive-area polygon intersection is retained, so one postcode can have
several regions. The percentage is:

```text
100 × area(postcode ∩ bioregion) / area(postcode)
```

Areas are calculated in GDA94 / Australian Albers (EPSG:3577), not in angular
EPSG:4326 coordinates. Results are rounded to the schema's two-decimal
precision. A stored `0.00` can therefore represent a real positive-area sliver
below 0.005%; raw overlap area is not stored in v1. `postcode_bioregion` is a
derived relationship, not a source boundary or property-level observation.
Percentages need not sum to exactly 100 because of source boundary/coastline
differences and rounding.
The loader counts invalid source geometries, repairs them with PostGIS
`ST_MakeValid`, extracts polygon components only, validates the result, and
records the repair count in `DATA_LOAD.notes`.

The v1 schema stores the region name but not `BIOREGCODE`, raw overlap
area, or the derivation's `load_id`. Provenance remains traceable through the
bioregion's `source_id` and the matching `DATA_LOAD.notes`; adding those fields
would require a reviewed future migration.

The superseded national service downloader is no longer used for new I1 data.

## Victorian EVC sources and relationship derivation

The EVC loader uses two official DataVic/DEECA Web Feature Service layers:

- **Modelled 1750 EVC with Bioregional Conservation Status**:
  <https://discover.data.vic.gov.au/dataset/native-vegetation-modelled-1750-ecological-vegetation-classes-with-bioregional-conservation-sta>
  (`open-data-platform:nv1750_evcbcs`)
- **Modelled 2005 EVC with Bioregional Conservation Status**:
  <https://discover.data.vic.gov.au/dataset/native-vegetation-modelled-2005-ecological-vegetation-classes-with-bioregional-conservation-sta>
  (`open-data-platform:nv2005_evcbcs`)
- Provider: Victorian Department of Energy, Environment and Climate Action
- Access: <https://opendata.maps.vic.gov.au/geoserver/wfs>, WFS 2.0 GeoJSON
- Licence: Creative Commons Attribution 4.0 International (CC BY 4.0)
- Published CRS: GDA2020 (EPSG:7844); the WFS request returns EPSG:4326
- Source fields used: `veg_code`, `x_evcname`, `evc_bcs_desc`, `evc_code`,
  `bioregion`, `bioregion_code`, `geom`

`veg_code` is mapped to `evc_class.evc_code`, rather than the unqualified
`evc_code`, because it combines the bioregion code and EVC code (for example
`OtR_0030`). Bioregional conservation status belongs to that regional EVC
combination. `x_evcname` maps to `evc_name`, and `evc_bcs_desc` maps to
`conservation_status`. Separate `SOURCE` records are retained for the 1750 and
2005 products. `reference_year` is respectively 1750 or 2005.

The 1750 product is modelled pre-European vegetation-community context. The
2005 product is a later mapped/modelled native-vegetation extent assembled with
different inputs; it is not a second equivalent historical baseline, a direct
survey, or proof of clearing on an individual property. Neither product proves
that an individual plant species existed at a location, nor that it was lost.

For each selected postcode, the loader requests source polygons intersecting
its bounding box, then performs the exact intersection in PostGIS. Multiple
source fragments belonging to the same regional EVC are dissolved by summing
their positive intersection areas. The stored percentage is:

```text
100 × area(postcode ∩ regional EVC fragments) / area(postcode)
```

Areas use Australian Albers (EPSG:3577), and percentages are rounded to two
decimal places. The loader keeps all positive-area overlaps, including real
slivers that round to `0.00`; it does not force coverage to 100%. A lower 2005
total can represent areas outside the mapped native-vegetation extent.
Invalid source polygons are counted, repaired with `ST_MakeValid`, reduced to
polygon components and revalidated. Repair counts are recorded in
`DATA_LOAD.notes`.

The v1 ERD has no EVC geometry column, raw overlap-area column, or per-row load
identifier. Source geometry is therefore validated and processed in temporary
PostGIS tables, while the durable result retains the class, source,
`reference_year`, percentage and load audit. No schema change is made.

The 2005 service currently exposes substantially more features than the 1750
service. To prevent an accidental statewide multi-million-feature run, EVC
scope must be explicit:

```bash
# Recommended development/verification scope
python3 backend/db/ingestion/evc/load_evc.py --postcode 3233 --period both

# Repeat --postcode for a controlled batch
python3 backend/db/ingestion/evc/load_evc.py \
  --postcode 3233 --postcode 3232 --period 1750

# Statewide relationship build: explicit opt-in
python3 backend/db/ingestion/evc/load_evc.py --all-postcodes --period both
```

Responses are paged, cached by year and postcode under
`~/.cache/regrove/evc/`, and written atomically. Use `--offline` to require an
existing cache, or `--refresh` to replace it. Each period's database write is
transactional and rebuilds only the selected postcode/source/year rows, so a
rerun is idempotent and cannot silently delete another scope or period. A
failed run is retained in `DATA_LOAD` with error notes.

## Validate

Run dependency-free input checks:

```bash
python3 -m unittest backend/db/ingestion/tests/test_postcode_loader.py
python3 -m unittest backend/db/ingestion/tests/test_bioregion_loader.py
python3 -m unittest backend/db/ingestion/tests/test_evc_loader.py
python3 -m unittest backend/db/ingestion/tests/test_vicflora_plant_loader.py
```

The real-source/PostGIS EVC integration check is opt-in because it needs a
migrated database containing real postcode 3233 geometry and either network
access or cached EVC responses. It runs both periods twice, checks that 3233
has spatially derived relationships, validates percentage ranges and duplicate
prevention, and confirms the rerun leaves the same relationship set:

```bash
REGROVE_EVC_INTEGRATION=1 \
REGROVE_EVC_CACHE_DIR="$HOME/.cache/regrove/evc" \
python3 -m unittest backend/db/ingestion/tests/test_evc_integration.py -v
```

Inspect postcode 3233 after a real load:

```bash
psql -X -v ON_ERROR_STOP=1 -v postcode=3233 \
  -f backend/db/ingestion/postcode/validate_postcode.sql
psql -X -v ON_ERROR_STOP=1 -v postcode=3233 \
  -f backend/db/ingestion/bioregion/validate_bioregion.sql
psql -X -v ON_ERROR_STOP=1 -v postcode=3233 \
  -f backend/db/ingestion/evc/validate_evc.sql
```

The validation query returns no row when the real source has not been loaded;
that must not be presented as a successful result. Its ecological detail and
coverage sections use the newest registered version of each named EVC product,
so historical source versions are not summed together. The provenance section
still lists every `SOURCE` version and every `DATA_LOAD` audit row.

## VicFlora plant taxonomy

The plant loader resolves an explicitly reviewed name list through the official
Royal Botanic Gardens Victoria **VicFlora GraphQL API**:

- Website and API documentation: <https://vicflora.rbg.vic.gov.au/api/>
- GraphQL endpoint: <https://vicflora.rbg.vic.gov.au/graphql>
- Provider: Royal Botanic Gardens Victoria, National Herbarium of Victoria
- API version: 1.0.0
- VicFlora text/data licence: Creative Commons Attribution 4.0 International
  (CC BY 4.0); API documentation/software is published under Apache 2.0
- Fields used: taxon-name/full name, accepted concept and identifier, rank,
  taxonomic status, preferred vernacular name, Victorian occurrence and
  establishment fields, Victorian endemic/introduced-occurrence flags, and
  EPBC/FFG status where present

This stage answers only “what accepted Victorian plant taxon does this reviewed
name denote?” It does not assert that a plant is locally indigenous, suitable
for postcode 3233, associated with an EVC, appropriate for a parcel, or useful
for a fauna guild.

The initial working name universe was extracted from Colac Otway Shire's
official **Apollo Bay/Skenes Creek Indigenous Species List**:
<https://www.colacotway.vic.gov.au/files/assets/public/trimfiles/my-property/environment-advice-to-the-public-external-authority-2015-2016/apollo-bay-skenes-creek-indigenous-species-list.pdf>.
Only the botanical-name identifiers needed for resolution were extracted, and
the PDF/name working files were kept outside the repository. Council-list
membership is not persisted as local suitability in this stage.

The input is UTF-8, one botanical name per line. A deliberately reviewed
spelling or nomenclatural query may be supplied as a second tab-separated
column:

```text
# original_name[tab]query_name
Acacia melanoxylon
Original spelling from source<TAB>Reviewed VicFlora query name
```

The first column is always preserved in the mapping report. The loader performs
whitespace normalisation only and requires an exact VicFlora taxon-name match.
It follows an exact synonym to its accepted concept, but never performs fuzzy
matching or silently repairs a spelling. Multiple accepted concepts are
reported as ambiguous. Unresolved names, duplicate inputs and accepted concepts
below species rank are reported and excluded from the v1 database load. The v1
`plant_species` table has no rank or source-name mapping columns, so this
conservative species-rank boundary and the external mapping report avoid a
schema change.

Run from the repository root after reviewing the input list:

```bash
python3 backend/db/ingestion/plants/load_vicflora_plants.py \
  --input /absolute/path/reviewed-plant-names.tsv
psql -X -v ON_ERROR_STOP=1 \
  -f backend/db/ingestion/plants/validate_plants.sql
```

API responses and the default mapping report are cached under
`~/.cache/regrove/vicflora/`, outside the repository. Use `--offline` to require
the cache, `--refresh` to re-query every supplied name, or `--cache`/`--report`
to choose explicit paths. Do not commit downloaded API responses or reports.

Accepted species populate `plant_species`. `native_status` is mapped only when
VicFlora consistently reports the accepted concept as present and native. A
separate value preserves the case where VicFlora also flags introduced
occurrences; missing or conflicting status remains null. This is Victorian
taxonomic/establishment status, not evidence of local indigeneity.
VicFlora occurrence/distribution information is supporting occurrence evidence,
not plant-recommendation evidence.

Selected non-null, directly sourced status fields populate `plant_trait` as
text: taxonomic status, occurrence status, establishment means, degree of
establishment, Victorian endemic flag, introduced-occurrence flag, EPBC status
and FFG status. No growth form, height, structure, flowering, fruit, seed,
nectar, soil, light, garden value or other unsupported trait is invented.

Each execution creates a separate `data_load` audit row. Re-running replaces
only this VicFlora source's controlled trait names for the resolved species and
upserts the accepted species name, so ecological/taxonomic rows do not
duplicate and traits from other sources are preserved. Original-to-accepted
mapping remains in the CSV report because the approved schema has no place to
store it.

The real-source/database rerun check is opt-in and requires an existing cache:

```bash
REGROVE_PLANT_INTEGRATION=1 \
REGROVE_VICFLORA_INPUT=/absolute/path/reviewed-plant-names.tsv \
REGROVE_VICFLORA_CACHE="$HOME/.cache/regrove/vicflora/taxon-names.json" \
python3 -m unittest \
  backend/db/ingestion/tests/test_vicflora_plant_integration.py -v
```

## Victorian Biodiversity Atlas 1-minute grid occurrence

The VBA loader reads the two official ESRI Shapefiles downloaded manually from
DataShare. It performs no web scraping and requires an explicit local path:

```bash
python3 backend/db/ingestion/vba/load_vba.py \
  --dataset flora --postcode 3233 \
  --input /absolute/path/VBA_FLORA_GRID_1M.shp
python3 backend/db/ingestion/vba/load_vba.py \
  --dataset fauna --postcode 3233 \
  --input /absolute/path/VBA_FAUNA_GRID_1M.shp
psql -X -v ON_ERROR_STOP=1 -v postcode=3233 \
  -f backend/db/ingestion/vba/validate_vba.sql
```

Both sources contain one polygon feature per 1-minute grid/taxon combination in
GDA94 (EPSG:4283). `CELL_ID`, `TAXON_ID`, `SCI_NAME`, `COMM_NAME`, `RECORDS`,
`FIRST_DATE`, `LAST_DATE` and `VERS_DATE` are read directly. Flora additionally
contains `VIC_LF`. The loader validates the complete actual field/type contract,
required SHP components, CRS, identifiers, positive counts, dates, duplicate
grid/taxon keys and polygon geometry before loading.

PostGIS intersects the full grid polygons with existing postcode polygons; no
centroid-only assignment is used. Every intersecting cell is contextual local-
area evidence. Full source `RECORDS` values are summed without area weighting:
partial grid overlap does not justify multiplying observations by overlap area.
Consequently, a record represented in a boundary cell may have occurred outside
the exact postcode boundary. This is not parcel-level evidence.

VBA fauna names populate `fauna_species` exactly and aggregate into
`fauna_occurrence_summary`. Source taxon ID/name ambiguities are excluded and
reported. The current fauna schema cannot persist the VBA taxon identifier.

Migration `003` adds only `plant_occurrence_summary`, because flora occurrence
cannot be represented honestly in `plant_trait`, `local_plant_suitability` or
`plant_resource_evidence`. Flora rows are persisted only when `SCI_NAME` exactly
matches an existing VicFlora-backed `plant_species`; unmatched and ambiguous
names remain in the CSV report. No fuzzy matching or new suitability assertion
is made.

The default reports are written outside the repository under
`~/.cache/regrove/vba/`. Every run creates a `data_load` audit. Scoped reruns
delete and rebuild only that source/postcode summary set, preventing duplicates
without deleting unrelated occurrence data.

Scientific interpretation is mandatory:

- `RECORDS` is a count of documented occurrence/observation records, not abundance.
- More records do not automatically mean more individuals.
- No occurrence row does not prove species absence.
- Intersecting 1-minute-grid evidence is local-area context, not an exact property observation.
- Flora occurrence is not planting suitability or a recommendation.
- Fauna occurrence does not prove that a residential garden can support the species.

Run the source checks with:

```bash
python3 -m unittest backend/db/ingestion/tests/test_vba_loader.py -v
REGROVE_VBA_INTEGRATION=1 \
REGROVE_VBA_FLORA_SHP=/absolute/path/VBA_FLORA_GRID_1M.shp \
REGROVE_VBA_FAUNA_SHP=/absolute/path/VBA_FAUNA_GRID_1M.shp \
python3 -m unittest backend/db/ingestion/tests/test_vba_integration.py -v
```

## Next stages (not implemented)

1. Review unresolved council-list names and any proposed corrected query names.
2. Establish evidence-based local suitability before writing
   `local_plant_suitability`; VicFlora taxonomy alone cannot provide it.
3. Assess separately sourced plant characteristics only after their definitions,
   units, coverage and provenance have been reviewed.

No unverified source field is specified here. EVC is vegetation-community
context, not proof of individual historical plant presence or loss. Local-area
evidence is not a property-level observation. Plant candidates are derived
outputs, not guaranteed ecological outcomes. Future occurrence counts must not
be treated as abundance, and missing occurrence records must not be treated as
species absence.
