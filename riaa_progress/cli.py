from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .estimator import analyze_folder, load_source_codes
from .reporting import format_summary, save_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="riaa-progress",
        description=(
            "Estimate streaming-equivalent RIAA progress from selected "
            "BMI statement performance rows."
        ),
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default="BMI Statements",
        help="Folder containing BMI statement CSV files.",
    )
    parser.add_argument(
        "--sources",
        default="config/riaa_sources.txt",
        help="Text file with accepted PERF SOURCE codes.",
    )
    parser.add_argument(
        "--country",
        default="UNITED STATES",
        help="COUNTRY OF PERFORMANCE value to include.",
    )
    parser.add_argument(
        "--output",
        default="output/riaa_progress_summary.csv",
        help="CSV report path.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on the first malformed statement instead of skipping it.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        source_codes = load_source_codes(Path(args.sources))
        result = analyze_folder(
            Path(args.folder),
            source_codes=source_codes,
            country=args.country,
            strict=args.strict,
        )
        save_csv(result.summary, Path(args.output))
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(format_summary(result.summary))
    print(
        f"\nProcessed {result.files_processed} CSV file(s). "
        f"Saved report to {args.output}"
    )

    if result.files_skipped:
        print("\nSkipped files:")
        for warning in result.files_skipped:
            print(f"  - {warning}")

    print(
        "\nImportant: this is a heuristic progress estimate from the supplied "
        "BMI statement data, not an official RIAA certification result."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
