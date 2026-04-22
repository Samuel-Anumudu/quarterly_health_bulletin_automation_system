from pathlib import Path
from typing import List

import pandas as pd


def latest_quarter(values: pd.Series) -> str:
    s = values.dropna().astype(str)
    if len(s) == 0:
        raise ValueError("No reporting_quarter values found")
    p = pd.PeriodIndex(s, freq="Q")
    return str(p.max())


def safe_rate(numer: pd.Series, denom: pd.Series, multiplier: float) -> pd.Series:
    numer = pd.to_numeric(numer, errors="coerce")
    denom = pd.to_numeric(denom, errors="coerce")
    out = (numer / denom) * multiplier
    out = out.where(denom > 0)
    return out


def to_markdown_table(df: pd.DataFrame, cols: List[str], n: int) -> str:
    view = df.loc[:, [c for c in cols if c in df.columns]].head(n).copy()
    headers = view.columns.tolist()

    def esc(v: str) -> str:
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

    rows = view.values.tolist()
    out = []
    out.append("| " + " | ".join(esc(h) for h in headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(esc(fmt(v)) for v in r) + " |")
    return "\n".join(out)


def main() -> None:
    base = Path(__file__).resolve().parent
    inp = base / "outputs" / "phase2_joined_quarterly.csv"
    out_dir = base / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Phase 3 intentionally reads the Phase 2 “staging” output so we only define metrics once.
    df = pd.read_csv(inp)
    q = latest_quarter(df["reporting_quarter"])
    # Bulletins are usually consumed per period, so we default to the latest quarter for a 1-row-per-facility view.
    df_q_raw = df[df["reporting_quarter"].astype(str) == q].copy()

    if len(df_q_raw) == 0:
        raise RuntimeError(f"No rows found for quarter {q}")

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
    # Counts drive ranking/totals; treating missing as 0 makes “non-reporting” facilities explicit instead of dropping them.
    for c in count_cols:
        if c in df_q.columns:
            df_q[c] = pd.to_numeric(df_q[c], errors="coerce").fillna(0)

    df_q["stillbirth_rate_pct"] = safe_rate(df_q.get("stillbirths"), df_q.get("total_deliveries"), 100.0)

    top10 = df_q.sort_values(["total_deliveries", "facility_name"], ascending=[False, True]).head(10)
    bottom10_hmis = df_q.sort_values(["hmis_reporting_completeness", "facility_name"], ascending=[True, True]).head(10)

    hmis = pd.to_numeric(df_q["hmis_reporting_completeness"], errors="coerce")
    referral_feedback = pd.to_numeric(df_q["referral_feedback_rate"], errors="coerce")

    clinical_present_rate = float(df_q_raw["total_deliveries"].notna().mean()) if "total_deliveries" in df_q_raw.columns else float("nan")

    md = []
    md.append(f"# Phase 3 — Metrics (Latest Quarter: {q})")
    md.append("")
    md.append("## Top 10 Facilities (by total deliveries)")
    # Deliveries are used as a practical volume proxy because general OPD/IPD visits are not available in the sample data.
    md.append(to_markdown_table(top10, ["facility_id", "facility_name", "district", "province", "total_deliveries"], 10))
    md.append("")
    md.append("## Maternal Indicator (Stillbirth Rate)")
    md.append("- Definition: stillbirth_rate_pct = stillbirths / total_deliveries × 100 (only when total_deliveries > 0)")
    sb = df_q["stillbirth_rate_pct"]
    total_deliveries = float(df_q["total_deliveries"].sum()) if "total_deliveries" in df_q.columns else 0.0
    total_stillbirths = float(df_q["stillbirths"].sum()) if "stillbirths" in df_q.columns else 0.0
    overall_weighted = (total_stillbirths / total_deliveries * 100.0) if total_deliveries > 0 else float("nan")
    md.append(f"- Overall (delivery-weighted): {overall_weighted:.2f}%")
    md.append(f"- Across facilities: mean={sb.mean(skipna=True):.2f}%, median={sb.median(skipna=True):.2f}%")
    md.append("")
    md.append("Highest 10 stillbirth rates (for review):")
    hi10_sb = df_q.sort_values(["stillbirth_rate_pct", "facility_name"], ascending=[False, True]).head(10)
    md.append(to_markdown_table(hi10_sb, ["facility_id", "facility_name", "total_deliveries", "stillbirths", "stillbirth_rate_pct"], 10))
    md.append("")
    md.append("## Performance Metric (HMIS Reporting Completeness)")
    md.append("- Source field: hmis_reporting_completeness (0–100)")
    md.append(f"- Overall: mean={hmis.mean(skipna=True):.1f}, median={hmis.median(skipna=True):.1f}")
    md.append(f"- Facilities with missing HMIS completeness: {int(hmis.isna().sum())} / {len(df_q)}")
    md.append(f"- Referral feedback rate (0–100): mean={referral_feedback.mean(skipna=True):.1f}, missing={int(referral_feedback.isna().sum())}")
    md.append("")
    md.append("Lowest 10 HMIS completeness scores (for follow-up):")
    md.append(to_markdown_table(bottom10_hmis, ["facility_id", "facility_name", "district", "hmis_reporting_completeness"], 10))
    md.append("")
    md.append("## Reporting Coverage (Clinical Presence)")
    md.append(f"- Facilities with a clinical record for {q}: {clinical_present_rate*100:.1f}%")
    md.append("")

    out_md = out_dir / f"phase3_metrics_{q}.md"
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    out_top10 = out_dir / f"phase3_top10_facilities_{q}.csv"
    top10.loc[:, ["facility_id", "facility_name", "district", "province", "total_deliveries"]].to_csv(out_top10, index=False)

    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_top10}")


if __name__ == "__main__":
    main()
