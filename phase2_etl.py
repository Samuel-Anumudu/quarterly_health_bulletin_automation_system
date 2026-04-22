import csv
from pathlib import Path
from typing import List, Optional

import pandas as pd


DELIMITER_CANDIDATES = [",", ";", "\t", "|"]


def sniff_delimiter(path: Path) -> str:
    try:
        sample = path.read_text(encoding="utf-8", errors="ignore")[:20000]
        dialect = csv.Sniffer().sniff(sample, delimiters=DELIMITER_CANDIDATES)
        if dialect.delimiter in DELIMITER_CANDIDATES:
            return dialect.delimiter
    except Exception:
        pass
    return ","


def read_csv_forgiving(path: Path, nrows: Optional[int] = None) -> pd.DataFrame:
    sep = sniff_delimiter(path)
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return pd.read_csv(
                path,
                sep=sep,
                engine="python",
                dtype="string",
                keep_default_na=True,
                na_values=["", "NA", "N/A", "null", "None", "nan", "NaN"],
                nrows=nrows,
                on_bad_lines="skip",
            )
        except Exception:
            continue
    return pd.read_csv(
        path,
        sep=sep,
        engine="python",
        dtype="string",
        keep_default_na=True,
        nrows=nrows,
        on_bad_lines="skip",
    )


def normalize_series(s: pd.Series) -> pd.Series:
    return (
        s.astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "NaN": pd.NA, "None": pd.NA, "null": pd.NA})
    )


def parse_percent_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            continue
        s = normalize_series(out[c]).astype(str).str.replace("%", "", regex=False)
        out[c] = pd.to_numeric(s, errors="coerce")
    return out


def parse_date_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            continue
        s = normalize_series(out[c])
        s = s.replace({"Never": pd.NA, "never": pd.NA})
        out[c] = pd.to_datetime(s, errors="coerce")
    return out


def to_numeric_columns(df: pd.DataFrame, exclude: List[str]) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        if c in exclude:
            continue
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def aggregate_clinical_quarterly(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = parse_date_columns(df, ["reporting_month"])
    df["reporting_quarter"] = df["reporting_month"].dt.to_period("Q").astype("string")

    numeric_exclude = ["facility_id", "reporting_month", "reporting_quarter"]
    df = to_numeric_columns(df, exclude=numeric_exclude)

    sum_cols = [c for c in df.columns if c not in numeric_exclude and c != "avg_gestational_age"]
    agg_map = {c: "sum" for c in sum_cols}
    if "avg_gestational_age" in df.columns:
        agg_map["avg_gestational_age"] = "mean"

    grouped = (
        df.dropna(subset=["facility_id", "reporting_quarter"])
        .groupby(["facility_id", "reporting_quarter"], as_index=False)
        .agg(agg_map)
    )
    return grouped


def main() -> None:
    base = Path(__file__).resolve().parent
    data_dir = base / "data"
    out_dir = base / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Prototype goal: keep everything in Pandas (no DB) so we can validate the reporting workflow quickly.
    facilities = read_csv_forgiving(data_dir / "facilities.csv")
    governance = read_csv_forgiving(data_dir / "governance.csv")
    healthcare = read_csv_forgiving(data_dir / "healthcare_workers.csv")
    operations = read_csv_forgiving(data_dir / "operations.csv")
    clinical = read_csv_forgiving(data_dir / "clinical_neonatal.csv")

    # Parse percent fields as 0–100 for readability in reports.
    governance = parse_percent_columns(
        governance,
        [
            "death_audits_conducted_pct",
            "staff_trained_on_protocol_pct",
            "hmis_reporting_completeness",
            "bag_mask_ventilation_competency",
            "thermal_care_protocol_compliance",
            "infection_prevention_score",
        ],
    )
    operations = parse_percent_columns(operations, ["referral_feedback_rate"])

    # Parse dates, treating "Never" as missing.
    governance = parse_date_columns(governance, ["protocol_last_updated"])
    healthcare = parse_date_columns(healthcare, ["last_neonatal_training_date"])

    clinical_q = aggregate_clinical_quarterly(clinical)

    quarters = sorted(clinical_q["reporting_quarter"].dropna().astype(str).unique().tolist())
    if not quarters:
        quarters = []

    # We build an explicit facility×quarter grid so missing clinical reporting stays visible (instead of dropping rows).
    facilities_ids = facilities.loc[:, ["facility_id"]].copy()
    facilities_ids["_k"] = 1
    quarters_df = pd.DataFrame({"reporting_quarter": quarters})
    quarters_df["_k"] = 1
    grid = facilities_ids.merge(quarters_df, on="_k", how="left").drop(columns=["_k"])

    # LEFT JOINs preserve the facility universe; missing values represent gaps we may want to follow up on.
    joined_q = grid.merge(facilities, on="facility_id", how="left")
    joined_q = joined_q.merge(governance, on="facility_id", how="left")
    joined_q = joined_q.merge(healthcare, on="facility_id", how="left")
    joined_q = joined_q.merge(operations, on="facility_id", how="left")
    joined_q = joined_q.merge(clinical_q, on=["facility_id", "reporting_quarter"], how="left")

    out_csv = out_dir / "phase2_joined_quarterly.csv"
    joined_q.to_csv(out_csv, index=False)

    print("Phase 2 ETL complete.")
    print(f"- Facilities rows: {len(facilities)}")
    print(f"- Joined rows (facility_id x quarter): {len(joined_q)}")
    print(f"Wrote: {out_csv}")


if __name__ == "__main__":
    main()
