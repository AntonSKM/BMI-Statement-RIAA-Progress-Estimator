from pathlib import Path

from riaa_progress.estimator import analyze_folder, load_source_codes


def test_example_aggregation() -> None:
    root = Path(__file__).resolve().parents[1]
    sources = load_source_codes(root / "config" / "riaa_sources.txt")

    result = analyze_folder(root / "examples" / "statements", source_codes=sources)

    dream = result.summary.loc[
        result.summary["TITLE NAME"] == "Dream Control"
    ].iloc[0]

    assert dream["OBSERVED_US_STREAM_COUNT"] == 52_483_200
    assert dream["EST_STREAM_EQUIVALENT_UNITS"] == 349_888
    assert dream["NEXT_MILESTONE"] == "Gold"
    assert dream["UNITS_REMAINING"] == 150_112


def test_non_configured_sources_are_excluded() -> None:
    root = Path(__file__).resolve().parents[1]
    sources = load_source_codes(root / "config" / "riaa_sources.txt")

    result = analyze_folder(root / "examples" / "statements", source_codes=sources)
    static = result.summary.loc[
        result.summary["TITLE NAME"] == "Static Hearts"
    ].iloc[0]

    assert static["OBSERVED_US_STREAM_COUNT"] == 4_500_000
