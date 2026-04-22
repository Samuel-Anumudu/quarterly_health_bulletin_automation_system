# Defense Notes — Quarterly Health Bulletin Prototype

## What this prototype proves
- Messy CSV inputs can be scanned, joined, and converted into defensible quarterly bulletin metrics using in-memory Pandas.
- The pipeline is intentionally lightweight and script-driven to prioritize clarity and speed of iteration over “app architecture”.

## Data model decisions (and why)
- Join key: `facility_id`
  - It is the only column present across all datasets and matched `facilities.facility_id` with full overlap in the scan.
- Anchor table: `facilities.csv`
  - It defines the facility universe; using it as the anchor preserves facilities even when other datasets are missing.
- Join type: LEFT JOINs from facilities → other datasets
  - Keeps all facilities and makes missingness visible (reporting gaps show up as missing values).
- Grain handling
  - `clinical_neonatal.csv` is time-series (monthly); the bulletin is quarterly.
  - Clinical data is aggregated to quarter first, then joined as `facility_id × reporting_quarter`.
  - The Phase 2 output is a full facility×quarter grid so missing clinical data for a quarter remains visible rather than silently dropping facilities.

## Parsing rules (chosen for pragmatism)
- Percent strings like `89%`
  - Converted to numeric 0–100 for readability and to avoid repeated parsing later.
- Date fields that can contain `Never`
  - `Never` is treated as missing (`NaT`), not an error.

## Metrics (simple and defensible)
- Volume proxy: `total_deliveries`
  - No general OPD/IPD visits exist in the provided data; deliveries are the most consistent activity proxy available.
- Top 10 facilities
  - Ranked by quarterly `total_deliveries` for the selected quarter.
- Maternal indicator: Stillbirth rate
  - `stillbirths / total_deliveries × 100` (only defined when total_deliveries > 0).
  - Presented as delivery-weighted overall rate plus facility-level distribution.
- Performance metric: HMIS reporting completeness
  - Uses `hmis_reporting_completeness` (0–100).

## UI scope (kept intentionally minimal)
- One page Streamlit view to make results easy to inspect and export.
- Default quarter is the latest available quarter.
- Includes only:
  - KPIs
  - Top 10 table
  - One chart
  - A couple of optional drill-down tables (in expanders)

## Validation & export behavior
- Hard errors (stop rendering): missing input file, missing required columns, invalid quarter format.
- Warnings (render continues): percent fields outside 0–100, negative count values, missing facilities in a quarter.
- Exports:
  - Top 10 CSV
  - Full facility-quarter CSV for the selected quarter
  - Markdown bulletin summary

## Known limitations (what I would do next if this were not a prototype)
- The pipeline assumes consistent semantics of fields across time (e.g., what “completeness” means); deeper data dictionary alignment would be needed for production.
- No advanced outlier detection or statistical modeling; the goal is practical reporting.
- Dependency management is minimal (requirements.txt) and not a production packaging setup.

