from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

import pandas as pd


REQUIRED_COLUMNS = {
    "COUNTRY OF PERFORMANCE",
    "PERF SOURCE",
    "TITLE NAME",
    "PERF COUNT",
}

STREAMS_PER_UNIT = 150
GOLD_UNITS = 500_000
PLATINUM_UNITS = 1_000_000
DIAMOND_UNITS = 10_000_000


@dataclass(frozen=True)
class AnalysisResult:
    summary: pd.DataFrame
    files_processed: int
    files_skipped: tuple[str, ...]


def load_source_codes(path: Path) -> set[str]:
    codes: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            value = line.strip()
            if value and not value.startswith("#"):
                codes.add(value.upper())
    if not codes:
        raise ValueError(f"No source codes found in {path}")
    return codes


def _read_statement(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str)

    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(
            f"{path.name}: missing required column(s): "
            + ", ".join(sorted(missing))
        )

    frame = frame.copy()
    for column in ("COUNTRY OF PERFORMANCE", "PERF SOURCE", "TITLE NAME"):
        frame[column] = frame[column].fillna("").astype(str).str.strip()

    numeric = (
        frame["PERF COUNT"]
        .fillna("")
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    frame["PERF COUNT"] = pd.to_numeric(numeric, errors="coerce")
    frame = frame.dropna(subset=["PERF COUNT"])
    return frame


def _next_milestone(units: int) -> tuple[str, int]:
    if units < GOLD_UNITS:
        return "Gold", GOLD_UNITS
    if units < PLATINUM_UNITS:
        return "Platinum", PLATINUM_UNITS
    if units < DIAMOND_UNITS:
        next_million = ((units // PLATINUM_UNITS) + 1) * PLATINUM_UNITS
        if next_million >= DIAMOND_UNITS:
            return "Diamond", DIAMOND_UNITS
        return f"{next_million // PLATINUM_UNITS}× Platinum", next_million
    return "Diamond reached", DIAMOND_UNITS


def _decorate(summary: pd.DataFrame) -> pd.DataFrame:
    decorated = summary.copy()
    decorated["EST_STREAM_EQUIVALENT_UNITS"] = (
        decorated["OBSERVED_US_STREAM_COUNT"] // STREAMS_PER_UNIT
    ).astype("int64")

    milestone_names: list[str] = []
    milestone_units: list[int] = []
    progress: list[float] = []
    remaining: list[int] = []

    for units in decorated["EST_STREAM_EQUIVALENT_UNITS"].tolist():
        name, target = _next_milestone(int(units))
        milestone_names.append(name)
        milestone_units.append(target)
        progress.append(round((units / target) * 100, 2) if target else 0.0)
        remaining.append(max(target - int(units), 0))

    decorated["NEXT_MILESTONE"] = milestone_names
    decorated["MILESTONE_UNITS"] = milestone_units
    decorated["PROGRESS_PERCENT"] = progress
    decorated["UNITS_REMAINING"] = remaining
    return decorated


def analyze_folder(
    folder: Path,
    *,
    source_codes: set[str],
    country: str = "UNITED STATES",
    strict: bool = False,
) -> AnalysisResult:
    csv_files = sorted(folder.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {folder}")

    per_file: list[pd.DataFrame] = []
    skipped: list[str] = []
    country_norm = country.strip().upper()
    sources_norm = {source.strip().upper() for source in source_codes}

    for path in csv_files:
        try:
            frame = _read_statement(path)
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            if strict:
                raise
            skipped.append(str(exc))
            continue

        mask = (
            frame["COUNTRY OF PERFORMANCE"].str.upper().eq(country_norm)
            & frame["PERF SOURCE"].str.upper().isin(sources_norm)
        )
        filtered = frame.loc[mask, ["TITLE NAME", "PERF COUNT"]].copy()
        if filtered.empty:
            continue

        grouped = (
            filtered.groupby("TITLE NAME", as_index=False)["PERF COUNT"]
            .sum()
            .rename(columns={"PERF COUNT": "OBSERVED_US_STREAM_COUNT"})
        )
        per_file.append(grouped)

    if per_file:
        combined = pd.concat(per_file, ignore_index=True)
        summary = (
            combined.groupby("TITLE NAME", as_index=False)["OBSERVED_US_STREAM_COUNT"]
            .sum()
            .sort_values("OBSERVED_US_STREAM_COUNT", ascending=False)
            .reset_index(drop=True)
        )
        summary["OBSERVED_US_STREAM_COUNT"] = (
            summary["OBSERVED_US_STREAM_COUNT"].round().astype("int64")
        )
        summary = _decorate(summary)
    else:
        summary = pd.DataFrame(
            columns=[
                "TITLE NAME",
                "OBSERVED_US_STREAM_COUNT",
                "EST_STREAM_EQUIVALENT_UNITS",
                "NEXT_MILESTONE",
                "MILESTONE_UNITS",
                "PROGRESS_PERCENT",
                "UNITS_REMAINING",
            ]
        )

    return AnalysisResult(
        summary=summary,
        files_processed=len(csv_files) - len(skipped),
        files_skipped=tuple(skipped),
    )
