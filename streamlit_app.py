from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
PHASE2_CSV = BASE_DIR / "outputs" / "phase2_joined_quarterly.csv"


def latest_quarter(values: pd.Series) -> str:
    s = values.dropna().astype(str)
    if len(s) == 0:
        raise ValueError("No reporting_quarter values found")
    p = pd.PeriodIndex(s, freq="Q")
    return str(p.max())


def safe_rate_pct(numer: pd.Series, denom: pd.Series) -> float:
    numer = pd.to_numeric(numer, errors="coerce").fillna(0)
    denom = pd.to_numeric(denom, errors="coerce").fillna(0)
    d = float(denom.sum())
    if d <= 0:
        return float("nan")
    return float(numer.sum()) / d * 100.0


def load_phase2() -> pd.DataFrame:
    if "phase2_df" not in st.session_state:
        st.session_state["phase2_df"] = pd.read_csv(PHASE2_CSV)
    return st.session_state["phase2_df"]

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def df_to_markdown_table(df: pd.DataFrame, cols: list[str], n: int) -> str:
    view = df.loc[:, [c for c in cols if c in df.columns]].head(n).copy()
    headers = view.columns.tolist()
    rows = view.values.tolist()

    def esc(v) -> str:
        return str(v).replace("|", "\\|").replace("\n", " ")

    def fmt(v) -> str:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        try:
            fv = float(v)
            if fv.is_integer():
                return str(int(fv))
            return f"{fv:.2f}"
        except Exception:
            return str(v)

    out = []
    out.append("| " + " | ".join(esc(h) for h in headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(esc(fmt(v)) for v in r) + " |")
    return "\n".join(out)


def validate_phase2(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    required_cols = {
        "facility_id",
        "facility_name",
        "district",
        "province",
        "reporting_quarter",
        "total_deliveries",
        "stillbirths",
        "hmis_reporting_completeness",
    }
    missing = sorted([c for c in required_cols if c not in df.columns])
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")

    if "reporting_quarter" in df.columns:
        quarters = df["reporting_quarter"].dropna().astype(str)
        if len(quarters) == 0:
            errors.append("No reporting_quarter values found.")
        else:
            try:
                pd.PeriodIndex(quarters.unique().tolist(), freq="Q")
            except Exception:
                errors.append("reporting_quarter values are not parseable as quarters (expected like 2024Q4).")

    for c in ["hmis_reporting_completeness", "referral_feedback_rate"]:
        if c not in df.columns:
            continue
        s = pd.to_numeric(df[c], errors="coerce")
        if s.notna().any():
            mn = float(s.min(skipna=True))
            mx = float(s.max(skipna=True))
            if mn < 0 or mx > 100:
                warnings.append(f"{c} has values outside 0–100 (min={mn:.1f}, max={mx:.1f}).")

    for c in ["total_deliveries", "stillbirths"]:
        if c not in df.columns:
            continue
        s = pd.to_numeric(df[c], errors="coerce")
        if (s < 0).any():
            warnings.append(f"{c} contains negative values.")

    return errors, warnings


def main() -> None:
    st.set_page_config(page_title="Quarterly Health Bulletin (Prototype)", layout="wide")

    # This is intentionally a “thin” UI: one page that reads a prepared dataset and displays the headline metrics.
    st.title("Quarterly Health Bulletin (Prototype)")
    st.caption("Minimal view: one quarter, key metrics, and a small set of tables/charts.")

    # We read the Phase 2 output file to keep the prototype simple:
    # Phase 2 already standardizes joins and quarter aggregation, so Phase 4 can focus on reporting.
    if not PHASE2_CSV.exists():
        st.error("Missing outputs/phase2_joined_quarterly.csv. Run: python phase2_etl.py")
        return

    df = load_phase2()
    # Validation is basic on purpose: it catches broken inputs early without turning this into a framework.
    errors, warns = validate_phase2(df)

    if errors:
        st.error("Input validation failed:")
        for e in errors:
            st.write(f"- {e}")
        return
    if warns:
        st.warning("Input validation warnings:")
        for w in warns:
            st.write(f"- {w}")

    quarters = sorted(df["reporting_quarter"].dropna().astype(str).unique().tolist())
    if not quarters:
        st.error("No reporting_quarter values found in Phase 2 output.")
        return

    default_q = latest_quarter(df["reporting_quarter"])

    st.sidebar.header("Filter")
    # Defaulting to the latest quarter keeps the experience aligned with how bulletins are typically used:
    # start with the most recent period, allow optional look-back.
    q = st.sidebar.selectbox(
        "Reporting quarter",
        quarters,
        index=quarters.index(default_q) if default_q in quarters else len(quarters) - 1,
    )

    facilities_total = int(df["facility_id"].nunique())

    df_q_raw = df[df["reporting_quarter"].astype(str) == q].copy()
    facilities_in_q = int(df_q_raw["facility_id"].nunique()) if len(df_q_raw) else 0
    if facilities_in_q != facilities_total:
        st.warning(f"Facilities present for {q}: {facilities_in_q} / {facilities_total}")

    count_cols = [
        "total_deliveries",
        "live_births",
        "stillbirths",
        "neonatal_deaths_0_7d",
        "neonatal_deaths_8_28d",
        "preterm_births_28_32w",
        "preterm_births_32_37w",
        "apgar_less_7_at_5min",
        "birth_weight_less_2500g",
    ]

    df_q = df_q_raw.copy()
    # For count-like fields, treating missing as 0 makes ranking and totals stable and transparent.
    for c in count_cols:
        if c in df_q.columns:
            df_q[c] = pd.to_numeric(df_q[c], errors="coerce").fillna(0)

    df_q["stillbirth_rate_pct"] = (
        pd.to_numeric(df_q["stillbirths"], errors="coerce")
        / pd.to_numeric(df_q["total_deliveries"], errors="coerce").replace({0: pd.NA})
        * 100.0
    )

    top10 = df_q.sort_values(["total_deliveries", "facility_name"], ascending=[False, True]).head(10)
    bottom10_hmis = df_q.sort_values(
        ["hmis_reporting_completeness", "facility_name"], ascending=[True, True]
    ).head(10)

    total_deliveries = int(df_q["total_deliveries"].sum())
    stillbirth_rate_weighted = safe_rate_pct(df_q["stillbirths"], df_q["total_deliveries"])
    hmis = pd.to_numeric(df_q["hmis_reporting_completeness"], errors="coerce")
    referral_feedback = (
        pd.to_numeric(df_q["referral_feedback_rate"], errors="coerce")
        if "referral_feedback_rate" in df_q.columns
        else pd.Series(dtype="float64")
    )

    report_md = "\n".join(
        [
            "# Quarterly Health Bulletin (Prototype)",
            f"Quarter: {q}",
            "",
            "## Key metrics",
            f"- Total deliveries: {total_deliveries}",
            f"- Stillbirth rate (delivery-weighted): {stillbirth_rate_weighted:.2f}%",
            f"- HMIS completeness (mean): {hmis.mean(skipna=True):.1f}",
            (
                f"- Referral feedback rate (mean): {referral_feedback.mean(skipna=True):.1f}"
                if len(referral_feedback) > 0
                else "- Referral feedback rate (mean): (not available)"
            ),
            "",
            "## Top 10 facilities by deliveries",
            "",
            df_to_markdown_table(
                top10.loc[:, ["facility_id", "facility_name", "district", "province", "total_deliveries"]],
                ["facility_id", "facility_name", "district", "province", "total_deliveries"],
                10,
            ),
            "",
        ]
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Quarter", q)
    col2.metric("Total deliveries", f"{total_deliveries:,}")
    col3.metric("Stillbirth rate (weighted)", f"{stillbirth_rate_weighted:.2f}%")
    col4.metric("HMIS completeness (mean)", f"{hmis.mean(skipna=True):.1f}")

    st.sidebar.header("Exports")
    # Exports are part of the prototype value: the user can take results straight into the bulletin workflow.
    st.sidebar.download_button(
        "Download Top 10 (CSV)",
        data=df_to_csv_bytes(
            top10.loc[:, ["facility_id", "facility_name", "district", "province", "total_deliveries"]]
        ),
        file_name=f"top10_deliveries_{q}.csv",
        mime="text/csv",
    )
    st.sidebar.download_button(
        "Download Facilities (CSV)",
        data=df_to_csv_bytes(df_q),
        file_name=f"facility_quarter_{q}.csv",
        mime="text/csv",
    )
    st.sidebar.download_button(
        "Download Bulletin (MD)",
        data=report_md,
        file_name=f"bulletin_{q}.md",
        mime="text/markdown",
    )

    st.subheader("Top 10 facilities by deliveries")
    st.dataframe(
        top10.loc[:, ["facility_id", "facility_name", "district", "province", "total_deliveries"]],
    )

    # A single chart is enough to make the ranking immediately scannable in a bulletin context.
    chart_df = top10.loc[:, ["facility_name", "total_deliveries"]].set_index("facility_name")
    st.bar_chart(chart_df)

    with st.expander("Maternal indicator details (stillbirth rate)", expanded=False):
        st.caption("Definition: stillbirths / total_deliveries × 100 (facility-level).")
        hi10_sb = df_q.sort_values(["stillbirth_rate_pct", "facility_name"], ascending=[False, True]).head(10)
        st.dataframe(
            hi10_sb.loc[
                :, ["facility_id", "facility_name", "total_deliveries", "stillbirths", "stillbirth_rate_pct"]
            ],
        )

    with st.expander("Performance follow-up (HMIS completeness)", expanded=False):
        st.caption("HMIS completeness is stored as 0–100 in Phase 2.")
        if len(referral_feedback) > 0:
            st.write(f"Referral feedback rate (mean): {referral_feedback.mean(skipna=True):.1f}")
        st.dataframe(
            bottom10_hmis.loc[:, ["facility_id", "facility_name", "district", "hmis_reporting_completeness"]],
        )


if __name__ == "__main__":
    main()
