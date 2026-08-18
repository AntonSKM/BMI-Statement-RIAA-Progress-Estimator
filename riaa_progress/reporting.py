from __future__ import annotations

from pathlib import Path

import pandas as pd


def format_summary(summary: pd.DataFrame) -> str:
    if summary.empty:
        return "No matching U.S. performance rows were found."

    lines = []
    header = (
        f"{'TITLE':<28} {'OBSERVED STREAMS':>18} "
        f"{'EST. UNITS':>12} {'NEXT':>16} {'PROGRESS':>10}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    for row in summary.itertuples(index=False, name=None):
        title, streams, units, milestone, _, progress, _ = row
        title = str(title)
        if len(title) > 28:
            title = title[:25] + "..."

        lines.append(
            f"{title:<28} {int(streams):>18,} {int(units):>12,} "
            f"{str(milestone):>16} {float(progress):>9.2f}%"
        )

    return "\n".join(lines)


def save_csv(summary: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False)
