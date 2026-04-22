import csv
import json
import os
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

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


def read_csv_forgiving(path: Path, nrows: Optional[int]) -> pd.DataFrame:
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


def safe_head_values(s: pd.Series, n: int = 5) -> List[str]:
    vals = normalize_series(s).dropna().unique().tolist()
    vals = [str(v) for v in vals[:n]]
    return vals


def parse_rate(s: pd.Series, kind: str) -> float:
    s2 = normalize_series(s).dropna()
    if len(s2) == 0:
        return 0.0
    if kind == "numeric":
        coerced = pd.to_numeric(s2, errors="coerce")
        return float(coerced.notna().mean())
    if kind == "datetime":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            coerced = pd.to_datetime(s2, errors="coerce")
        return float(coerced.notna().mean())
    if kind == "percent":
        pat = re.compile(r"^\s*\d+(\.\d+)?\s*%\s*$")
        return float(s2.astype(str).str.match(pat).mean())
    return 0.0


def is_binary_like(s: pd.Series) -> bool:
    s2 = normalize_series(s).dropna().astype(str).str.lower()
    if len(s2) == 0:
        return False
    uniq = set(s2.unique().tolist())
    binary_vocab = {"0", "1", "yes", "no", "true", "false", "y", "n"}
    return len(uniq) <= 3 and uniq.issubset(binary_vocab)


def id_value_rate(s: pd.Series) -> float:
    s2 = normalize_series(s).dropna().astype(str)
    if len(s2) == 0:
        return 0.0
    pats = [
        re.compile(r"^[0-9]{3,}$"),
        re.compile(r"^[A-Za-z]{2,6}[0-9]{2,6}$"),
        re.compile(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        ),
    ]
    matched = s2.apply(lambda v: any(p.match(v) for p in pats))
    return float(matched.mean())


NAME_HINTS = {
    "id": ["id", "code", "uuid", "facility_id", "site_id", "hf_id"],
    "name": ["name", "facility", "hospital", "center", "site"],
    "date": ["date", "month", "year", "quarter", "period", "updated"],
    "volume": ["patients", "visits", "admissions", "deliver", "birth", "referral", "volume", "caseload"],
    "maternal": ["mater", "preg", "deliver", "birth", "still", "obstet", "midwif", "c-section", "cs", "complic"],
    "performance": ["report", "complete", "timely", "audit", "score", "pct", "percent", "rate", "coverage"],
}


def name_hint_score(col_name: str, hint_key: str) -> int:
    n = col_name.strip().lower()
    score = 0
    for tok in NAME_HINTS.get(hint_key, []):
        if tok in {"id"}:
            if re.search(r"(^|[^a-z0-9])id($|[^a-z0-9])", n):
                score += 1
            continue
        if tok in n:
            score += 1
    return score


@dataclass
class ColumnProfile:
    name: str
    non_null: int
    missing_pct: float
    nunique: int
    uniqueness_ratio: float
    numeric_rate: float
    datetime_rate: float
    percent_rate: float
    binary_like: bool
    id_value_rate: float
    sample_values: List[str]


def profile_columns(df: pd.DataFrame) -> Dict[str, ColumnProfile]:
    out: Dict[str, ColumnProfile] = {}
    nrows = len(df)
    for c in df.columns.tolist():
        s = df[c]
        s_norm = normalize_series(s)
        non_null = int(s_norm.notna().sum())
        missing_pct = float(1 - (non_null / nrows)) if nrows else 0.0
        nunique = int(s_norm.dropna().nunique())
        uniqueness_ratio = float(nunique / non_null) if non_null else 0.0
        numeric_rate = parse_rate(s_norm, "numeric")
        datetime_rate = parse_rate(s_norm, "datetime")
        percent_rate = parse_rate(s_norm, "percent")
        out[c] = ColumnProfile(
            name=c,
            non_null=non_null,
            missing_pct=missing_pct,
            nunique=nunique,
            uniqueness_ratio=uniqueness_ratio,
            numeric_rate=numeric_rate,
            datetime_rate=datetime_rate,
            percent_rate=percent_rate,
            binary_like=is_binary_like(s_norm),
            id_value_rate=id_value_rate(s_norm),
            sample_values=safe_head_values(s_norm, n=5),
        )
    return out


def facility_id_candidates(
    df: pd.DataFrame, prof: Dict[str, ColumnProfile]
) -> List[Dict[str, Any]]:
    candidates = []
    for c, p in prof.items():
        if p.non_null == 0:
            continue
        id_hints = name_hint_score(c, "id")
        base = 0.0
        base += 2.0 * id_hints
        base += 1.5 * p.id_value_rate
        base += 1.0 * (1.0 - p.missing_pct)
        base += 1.0 * min(p.uniqueness_ratio, 1.0)
        if p.numeric_rate > 0.95 or p.datetime_rate > 0.8 or p.percent_rate > 0.8:
            base -= 0.5
        if (
            id_hints == 0
            and p.numeric_rate > 0.95
            and p.id_value_rate > 0.6
            and p.uniqueness_ratio < 0.4
        ):
            base -= 1.5
        candidates.append(
            {
                "column": c,
                "score": round(base, 3),
                "reasons": [
                    f"name_id_hints={id_hints}",
                    f"id_value_rate={p.id_value_rate:.2f}",
                    f"missing_pct={p.missing_pct:.2f}",
                    f"uniqueness_ratio={p.uniqueness_ratio:.2f}",
                ],
            }
        )
    candidates.sort(key=lambda d: d["score"], reverse=True)
    return candidates[:5]


def metric_candidates(prof: Dict[str, ColumnProfile], kind: str) -> List[Dict[str, Any]]:
    candidates = []
    for c, p in prof.items():
        if p.non_null == 0:
            continue
        base = 0.0
        base += 2.0 * name_hint_score(c, kind)
        if kind in ("volume", "maternal"):
            base += 1.0 * p.numeric_rate
            if p.percent_rate > 0.6:
                base -= 0.5
        if kind == "performance":
            base += 1.0 * max(p.percent_rate, p.numeric_rate)
            base += 0.5 * p.binary_like
        if kind == "maternal" and name_hint_score(c, "volume") > 0:
            base += 0.25
        if base <= 0:
            continue
        candidates.append(
            {
                "column": c,
                "score": round(base, 3),
                "reasons": [
                    f"name_hints={name_hint_score(c, kind)}",
                    f"numeric_rate={p.numeric_rate:.2f}",
                    f"percent_rate={p.percent_rate:.2f}",
                    f"binary_like={p.binary_like}",
                ],
            }
        )
    candidates.sort(key=lambda d: d["score"], reverse=True)
    return candidates[:7]


def join_match_rate(left_values: pd.Series, right_values_set: Set[str]) -> float:
    s = normalize_series(left_values).dropna().astype(str)
    if len(s) == 0:
        return 0.0
    return float(s.isin(right_values_set).mean())


def best_join_key(
    df: pd.DataFrame, facilities_id_sets: Dict[str, Set[str]]
) -> List[Dict[str, Any]]:
    results = []
    for fac_col, fac_set in facilities_id_sets.items():
        for c in df.columns.tolist():
            rate = join_match_rate(df[c], fac_set)
            if rate <= 0:
                continue
            results.append(
                {
                    "facilities_column": fac_col,
                    "other_column": c,
                    "match_rate": round(rate, 3),
                }
            )
    results.sort(key=lambda d: d["match_rate"], reverse=True)
    return results[:5]


def main() -> None:
    base = Path(__file__).resolve().parent
    data_dir = base / "data"
    out_dir = base / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted([p for p in data_dir.glob("*.csv")])
    if not files:
        raise SystemExit(f"No CSV files found in {data_dir}")

    frames: Dict[str, pd.DataFrame] = {}
    profiles: Dict[str, Dict[str, ColumnProfile]] = {}

    for p in files:
        df = read_csv_forgiving(p, nrows=None)
        frames[p.name] = df
        profiles[p.name] = profile_columns(df)

    facilities_name = "facilities.csv" if "facilities.csv" in frames else files[0].name
    facilities_df = frames[facilities_name]
    facilities_prof = profiles[facilities_name]
    fac_id_ranked = facility_id_candidates(facilities_df, facilities_prof)
    top_fac_id_cols = [d["column"] for d in fac_id_ranked[:3]]

    facilities_id_sets: Dict[str, Set[str]] = {}
    for c in top_fac_id_cols:
        facilities_id_sets[c] = set(
            normalize_series(facilities_df[c]).dropna().astype(str).unique().tolist()
        )

    summary = {"files": {}, "cross_file": {}}

    for fname, df in frames.items():
        prof = profiles[fname]
        cols = df.columns.tolist()
        fac_candidates = facility_id_candidates(df, prof)
        join_suggestions = []
        if fname != facilities_name and facilities_id_sets:
            join_suggestions = best_join_key(df, facilities_id_sets)
        summary["files"][fname] = {
            "nrows": int(len(df)),
            "ncols": int(len(cols)),
            "columns": cols,
            "facility_id_candidates": fac_candidates,
            "join_suggestions_against_facilities": join_suggestions,
            "patient_volume_candidates": metric_candidates(prof, "volume"),
            "maternal_indicator_candidates": metric_candidates(prof, "maternal"),
            "reporting_performance_candidates": metric_candidates(prof, "performance"),
            "column_profiles": {
                c: {
                    "non_null": p.non_null,
                    "missing_pct": round(p.missing_pct, 3),
                    "nunique": p.nunique,
                    "uniqueness_ratio": round(p.uniqueness_ratio, 3),
                    "numeric_rate": round(p.numeric_rate, 3),
                    "datetime_rate": round(p.datetime_rate, 3),
                    "percent_rate": round(p.percent_rate, 3),
                    "binary_like": p.binary_like,
                    "id_value_rate": round(p.id_value_rate, 3),
                    "sample_values": p.sample_values,
                }
                for c, p in prof.items()
            },
        }

    all_cols = {fname: set(frames[fname].columns.tolist()) for fname in frames}
    common_cols = set.intersection(*all_cols.values()) if all_cols else set()
    summary["cross_file"]["common_columns_all_files"] = sorted(common_cols)

    facility_id_presence = {}
    for fname, df in frames.items():
        present = [c for c in df.columns.tolist() if name_hint_score(c, "id") > 0]
        facility_id_presence[fname] = present[:10]
    summary["cross_file"]["columns_with_id_like_names"] = facility_id_presence

    md_lines = []
    md_lines.append("# Phase 1 — Schema Scan Summary")
    md_lines.append("")
    md_lines.append(f"Anchor table (assumed): **{facilities_name}**")
    md_lines.append("")
    md_lines.append("## Cross-file signals")
    md_lines.append(f"- Columns common to all files: {', '.join(summary['cross_file']['common_columns_all_files']) or '(none)'}")
    md_lines.append("- Top Facility ID candidates in facilities (ranked):")
    for d in fac_id_ranked:
        md_lines.append(f"  - {d['column']} (score={d['score']}): " + "; ".join(d["reasons"]))
    md_lines.append("")

    for fname in files:
        fn = fname.name
        s = summary["files"][fn]
        md_lines.append(f"## {fn}")
        md_lines.append(f"- Shape: {s['nrows']} rows × {s['ncols']} cols")
        md_lines.append(f"- Columns: {', '.join(s['columns'])}")
        md_lines.append("- Suggested Facility ID columns (within this file):")
        for d in s["facility_id_candidates"][:5]:
            md_lines.append(f"  - {d['column']} (score={d['score']}): " + "; ".join(d["reasons"]))
        if s["join_suggestions_against_facilities"]:
            md_lines.append("- Best join key matches against facilities (value overlap rate):")
            for d in s["join_suggestions_against_facilities"][:5]:
                md_lines.append(
                    f"  - facilities.{d['facilities_column']}  ⇐⇒  {fn}.{d['other_column']}  (match_rate={d['match_rate']})"
                )
        md_lines.append("- Candidate columns (patient volume):")
        for d in s["patient_volume_candidates"][:5]:
            md_lines.append(f"  - {d['column']} (score={d['score']}): " + "; ".join(d["reasons"]))
        md_lines.append("- Candidate columns (maternal indicators):")
        for d in s["maternal_indicator_candidates"][:5]:
            md_lines.append(f"  - {d['column']} (score={d['score']}): " + "; ".join(d["reasons"]))
        md_lines.append("- Candidate columns (reporting / performance):")
        for d in s["reporting_performance_candidates"][:5]:
            md_lines.append(f"  - {d['column']} (score={d['score']}): " + "; ".join(d["reasons"]))
        md_lines.append("")

    out_json = out_dir / "phase1_schema_summary.json"
    out_md = out_dir / "phase1_schema_summary.md"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("\n".join(md_lines))
    print("")
    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_json}")


if __name__ == "__main__":
    main()
