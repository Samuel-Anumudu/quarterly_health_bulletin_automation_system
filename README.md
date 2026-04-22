# Quarterly Health Bulletin Automation (Prototype)

This repo is a small, end-to-end prototype that takes DHIS2-like CSV exports and produces a quarterly “bulletin view”:

- Top facilities by volume (proxy: deliveries)
- One maternal indicator (stillbirth rate)
- One facility performance metric (reporting completeness)

It is intentionally lightweight: in-memory Pandas + a one-page Streamlit view.

## Live demo

- Streamlit app: https://quarterly-health-bulletin-automation-system.streamlit.app/

## What’s inside

- Phase 1 (Discovery): [phase1_scan.py](phase1_scan.py)
- Phase 2 (ETL/Join): [phase2_etl.py](phase2_etl.py)
- Phase 3 (Metrics): [phase3_metrics.py](phase3_metrics.py)
- Phase 4/5 (Dashboard + Validation + Export): [streamlit_app.py](streamlit_app.py)

Inputs live in `data/`. Generated outputs go to `outputs/`.

## Setup

Prereqs:

- Python 3.9+

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run locally (end-to-end)

1) Scan the input schemas (no assumptions about columns):

```bash
python phase1_scan.py
```

This writes:

- `outputs/phase1_schema_summary.md`
- `outputs/phase1_schema_summary.json`

2) Build the facility×quarter dataset (in-memory Pandas, LEFT JOINs):

```bash
python phase2_etl.py
```

This writes:

- `outputs/phase2_joined_quarterly.csv`

3) Compute metrics for the latest available quarter:

```bash
python phase3_metrics.py
```

This writes (example):

- `outputs/phase3_metrics_2024Q4.md`
- `outputs/phase3_top10_facilities_2024Q4.csv`

## Run the dashboard

Start Streamlit:

```bash
python -m streamlit run streamlit_app.py
```

What you’ll see:

- Defaults to the latest quarter
- Top 10 table + one bar chart
- Basic validation (missing columns, bad quarter format, out-of-range % warnings)
- Exports (CSV + Markdown bulletin)

If you get “Port 8501 is already in use”, run:

```bash
python -m streamlit run streamlit_app.py --server.port 8502
```

## Output demonstration

The deployed app reads `outputs/phase2_joined_quarterly.csv`. If you want to regenerate it locally, run `python phase2_etl.py`.
