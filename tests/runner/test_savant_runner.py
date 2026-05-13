"""Tests for the SavantRunner class."""

import io
import json
import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from savant_api_extractor.leaderboards import ETL_TIER_CONFIGS
from savant_api_extractor.runner.savant_runner import SavantRunner
from savant_api_extractor.utils.extraction_type import ExtractionType
from savant_api_extractor.utils.thresholds import ThresholdType


def _csv_response(text: str) -> MagicMock:
    """Build a MagicMock that quacks like a requests.Response for a CSV payload."""
    r = MagicMock()
    r.text = text
    r.raise_for_status = MagicMock()
    return r


def _build_url_router(
    splits_fixtures: dict[str, dict[str, str]],
    leaderboard_fixtures: dict[str, str],
):
    """Return a callable suitable for `mock_get.side_effect` that routes by URL.

    Used for tests where calls are made in non-deterministic order (the
    leaderboard pulls happen in parallel via ThreadPoolExecutor, so we can't
    rely on a fixed `side_effect` list).

    Args:
        splits_fixtures: e.g. {"batter": batters_split_fixtures,
                               "pitcher": pitchers_split_fixtures}
        leaderboard_fixtures: dict of {config.name: csv_text}
    """
    # Map leaderboard slug → config.name to look up the right fixture
    slug_to_name: dict[tuple[str, frozenset[tuple[str, str]]], str] = {}
    for cfg in ETL_TIER_CONFIGS:
        # Distinguish configs sharing a url_path (statcast batter vs pitcher)
        # by the union of their default_params (type/player_type).
        key = (cfg.url_path, frozenset(cfg.default_params.items()))
        slug_to_name[key] = cfg.name

    def _route(url: str, params: dict[str, Any] | None = None, **_: Any) -> MagicMock:
        params = params or {}
        if "statcast_search/csv" in url:
            player_type = params.get("player_type", "batter")
            role = "batter" if player_type == "batter" else "pitcher"
            if params.get("pitcher_throws") == "R" or params.get("batter_stands") == "R":
                opp = "R"
            elif params.get("pitcher_throws") == "L" or params.get("batter_stands") == "L":
                opp = "L"
            else:
                opp = "all"
            return _csv_response(splits_fixtures[role][opp])

        if "/leaderboard/" in url:
            slug = url.rsplit("/", 1)[-1]
            # Match by (slug, default_params) — strip `csv` + per-call overrides
            relevant = {
                k: v
                for k, v in params.items()
                if k not in {"csv", "year"}
            }
            # Find config whose default_params match this subset
            for (cfg_slug, cfg_params), cfg_name in slug_to_name.items():
                if cfg_slug != slug:
                    continue
                if dict(cfg_params) == relevant:
                    return _csv_response(leaderboard_fixtures[cfg_name])
            raise AssertionError(
                f"No leaderboard fixture matches {url!r} params={relevant}"
            )

        raise AssertionError(f"Unexpected URL in test mock: {url}")

    return _route


def test_runner_initialization(tmp_path: Path) -> None:
    runner = SavantRunner(
        season="2026",
        extraction_type="batters",
        threshold_type=ThresholdType.DEFAULT,
        output_dir=tmp_path,
    )

    assert runner.extraction_method == ExtractionType.BATTER
    assert runner.threshold_type == ThresholdType.DEFAULT
    assert runner.season == "2026"
    assert runner.output_dir == tmp_path


def test_runner_export_to_json_dataframe(
    tmp_path: Path,
    batters_all_fixture: str,
) -> None:
    runner = SavantRunner(
        season="2026",
        extraction_type="batters",
        output_dir=tmp_path,
    )
    df = pd.read_csv(io.StringIO(batters_all_fixture), low_memory=False)

    # Export expects a dictionary, not a single DataFrame
    output_paths = runner._export_to_json({"batters": df})  # pyright: ignore[reportPrivateUsage]

    assert len(output_paths) == 1
    # Check filename matches pattern: savant_batters_YYYY_MM_DD_HHMM.json
    assert re.match(
        r"savant_batters_\d{4}_\d{2}_\d{2}_\d{4}\.json", output_paths[0].name
    )
    data = json.loads(output_paths[0].read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == len(df)
    # Round-trip first row preserves the raw CSV's first record
    assert data[0]["player_name"] == df.iloc[0]["player_name"]
    assert data[0]["player_id"] == int(df.iloc[0]["player_id"])


def test_runner_run_batter_returns_dict(
    tmp_path: Path,
    batters_split_fixtures: dict[str, str],
) -> None:
    """Runner makes 3 HTTP calls per role (all → R → L) and concats them."""
    runner = SavantRunner(
        season="2026",
        extraction_type="batters",
        output_dir=tmp_path,
        include_leaderboards=False,  # focus this test on splits behavior
    )

    with patch("savant_api_extractor.handlers.base_handler.requests.get") as mock_get:
        # Order matches OPP_HAND_SPLITS = ("all", "R", "L")
        mock_get.side_effect = [
            _csv_response(batters_split_fixtures["all"]),
            _csv_response(batters_split_fixtures["R"]),
            _csv_response(batters_split_fixtures["L"]),
        ]

        results = runner.run()

    assert mock_get.call_count == 3
    assert list(results.keys()) == ["batters"]

    df = results["batters"]
    # Every batter row tagged with one of the three opp_hand values
    assert set(df["opp_hand"].unique()) == {"all", "R", "L"}
    # Player_type tagging applied uniformly
    assert (df["player_type"] == "batter").all()
    # Ohtani appears across all 3 splits (stable two-way player)
    ohtani_splits = set(df.loc[df["name"] == "Ohtani, Shohei", "opp_hand"])
    assert ohtani_splits == {"all", "R", "L"}

    # Find the file matching pattern: savant_batters_YYYY_MM_DD_HHMM.json
    output_files = list(tmp_path.glob("savant_batters_*.json"))
    assert len(output_files) == 1
    assert re.match(
        r"savant_batters_\d{4}_\d{2}_\d{2}_\d{4}\.json", output_files[0].name
    )

    data = json.loads(output_files[0].read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert data[0]["player_type"] == "batter"
    assert "opp_hand" in data[0]
    # Percentile-rank columns are no longer emitted at extract time.
    assert not any(k.endswith("_pct_rnk") for k in data[0].keys())
    assert {row["opp_hand"] for row in data} == {"all", "R", "L"}


def test_runner_run_all_exports_json(
    tmp_path: Path,
    batters_split_fixtures: dict[str, str],
    pitchers_split_fixtures: dict[str, str],
) -> None:
    """Full run hits 6 endpoints (2 roles × 3 splits) and writes 2 files."""
    runner = SavantRunner(
        season="2026",
        extraction_type="all",
        output_dir=tmp_path,
        include_leaderboards=False,  # focus this test on splits behavior
    )

    with patch("savant_api_extractor.handlers.base_handler.requests.get") as mock_get:
        # Runner iterates extraction_types [BATTER, PITCHER]; for each, splits all → R → L
        mock_get.side_effect = [
            _csv_response(batters_split_fixtures["all"]),
            _csv_response(batters_split_fixtures["R"]),
            _csv_response(batters_split_fixtures["L"]),
            _csv_response(pitchers_split_fixtures["all"]),
            _csv_response(pitchers_split_fixtures["R"]),
            _csv_response(pitchers_split_fixtures["L"]),
        ]

        results = runner.run()

    assert mock_get.call_count == 6
    assert "batters" in results and "pitchers" in results

    bdf = results["batters"]
    pdf = results["pitchers"]
    assert set(bdf["opp_hand"].unique()) == {"all", "R", "L"}
    assert set(pdf["opp_hand"].unique()) == {"all", "R", "L"}
    assert (bdf["player_type"] == "batter").all()
    assert (pdf["player_type"] == "pitcher").all()

    # Two output files, one per role
    batters_files = list(tmp_path.glob("savant_batters_*.json"))
    pitchers_files = list(tmp_path.glob("savant_pitchers_*.json"))
    assert len(batters_files) == 1
    assert len(pitchers_files) == 1
    assert re.match(
        r"savant_batters_\d{4}_\d{2}_\d{2}_\d{4}\.json", batters_files[0].name
    )
    assert re.match(
        r"savant_pitchers_\d{4}_\d{2}_\d{2}_\d{4}\.json", pitchers_files[0].name
    )

    batters_data = json.loads(batters_files[0].read_text(encoding="utf-8"))
    pitchers_data = json.loads(pitchers_files[0].read_text(encoding="utf-8"))

    assert isinstance(batters_data, list)
    assert isinstance(pitchers_data, list)
    assert len(batters_data) > 0
    assert len(pitchers_data) > 0
    assert batters_data[0]["player_type"] == "batter"
    assert pitchers_data[0]["player_type"] == "pitcher"
    # Percentile-rank columns are no longer emitted at extract time.
    assert not any(k.endswith("_pct_rnk") for k in batters_data[0].keys())
    assert not any(k.endswith("_pct_rnk") for k in pitchers_data[0].keys())


def test_runner_run_all_with_leaderboards(
    tmp_path: Path,
    batters_split_fixtures: dict[str, str],
    pitchers_split_fixtures: dict[str, str],
    leaderboard_fixtures: dict[str, str],
) -> None:
    """End-to-end: 6 split calls + 8 leaderboard calls → 10 output files."""
    runner = SavantRunner(
        season="2026",
        extraction_type="all",
        output_dir=tmp_path,
        include_leaderboards=True,
    )

    router = _build_url_router(
        splits_fixtures={
            "batter": batters_split_fixtures,
            "pitcher": pitchers_split_fixtures,
        },
        leaderboard_fixtures=leaderboard_fixtures,
    )

    with patch(
        "savant_api_extractor.handlers.base_handler.requests.get",
        side_effect=router,
    ) as mock_get:
        results = runner.run()

    # 6 split calls + 8 leaderboard calls
    assert mock_get.call_count == 14

    # Results dict has 2 split keys + 8 leaderboard keys
    expected_keys = {"batters", "pitchers"} | {c.name for c in ETL_TIER_CONFIGS}
    assert set(results.keys()) == expected_keys

    # One output file per result key
    for key in expected_keys:
        files = list(tmp_path.glob(f"savant_{key}_*.json"))
        assert len(files) == 1, f"expected one file for {key}, got {files}"

    # Spot-check leaderboard outputs round-trip cleanly
    statcast_batter_file = next(tmp_path.glob("savant_statcast_batter_*.json"))
    statcast_batter_rows = json.loads(statcast_batter_file.read_text())
    assert isinstance(statcast_batter_rows, list)
    assert len(statcast_batter_rows) > 0
    assert any(row["name"] == "Ohtani, Shohei" for row in statcast_batter_rows)

    # Pitch-arsenal-stats is long-format on pitch_type
    pas_file = next(tmp_path.glob("savant_pitch_arsenal_stats_batter_*.json"))
    pas_rows = json.loads(pas_file.read_text())
    ohtani_pas = [r for r in pas_rows if r["name"] == "Ohtani, Shohei"]
    assert len(ohtani_pas) > 1  # multiple pitch types faced


def test_runner_leaderboard_failure_logs_and_reraises(
    tmp_path: Path,
    batters_split_fixtures: dict[str, str],
    pitchers_split_fixtures: dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When a leaderboard pull fails, the runner logs which one failed and re-raises.

    Exercises `_extract_leaderboards`'s exception path (the `try/except Exception
    as e` block around `future.result()`). The split calls succeed normally; the
    leaderboard handler is patched to raise on the first call, simulating a Savant
    outage / parse failure for one of the leaderboards.
    """
    runner = SavantRunner(
        season="2026",
        extraction_type="all",
        output_dir=tmp_path,
        include_leaderboards=True,
    )

    with patch(
        "savant_api_extractor.handlers.base_handler.requests.get"
    ) as mock_get, patch.object(
        runner.leaderboard_handler,
        "extract",
        side_effect=RuntimeError("simulated leaderboard failure"),
    ):
        mock_get.side_effect = [
            _csv_response(batters_split_fixtures["all"]),
            _csv_response(batters_split_fixtures["R"]),
            _csv_response(batters_split_fixtures["L"]),
            _csv_response(pitchers_split_fixtures["all"]),
            _csv_response(pitchers_split_fixtures["R"]),
            _csv_response(pitchers_split_fixtures["L"]),
        ]

        with pytest.raises(RuntimeError, match="simulated leaderboard failure"):
            runner.run()

    # The runner logged which leaderboard failed before re-raising
    assert any(
        "failed: simulated leaderboard failure" in record.message
        for record in caplog.records
    ), f"expected failure log line; got records: {[r.message for r in caplog.records]}"


def test_runner_split_invariant_R_L_subset_of_all(
    tmp_path: Path,
    batters_split_fixtures: dict[str, str],
    pitchers_split_fixtures: dict[str, str],
) -> None:
    """Invariant: every player in vs_R or vs_L also appears in `all`.

    Before the threshold fix, this could fail silently — sub-threshold
    players appeared in R/L (ungated) but not in `all` (gated at min_pas=30),
    breaking downstream joins. Asserting the invariant here pins it as a
    structural guarantee. Scoped to splits behavior via
    `include_leaderboards=False` — leaderboard pulls are orthogonal to the
    split invariant being verified here.
    """
    runner = SavantRunner(
        season="2026",
        extraction_type="all",
        output_dir=tmp_path,
        include_leaderboards=False,
    )
    with patch("savant_api_extractor.handlers.base_handler.requests.get") as mock_get:
        mock_get.side_effect = [
            _csv_response(batters_split_fixtures["all"]),
            _csv_response(batters_split_fixtures["R"]),
            _csv_response(batters_split_fixtures["L"]),
            _csv_response(pitchers_split_fixtures["all"]),
            _csv_response(pitchers_split_fixtures["R"]),
            _csv_response(pitchers_split_fixtures["L"]),
        ]
        results = runner.run()

    for role, df in (("batters", results["batters"]), ("pitchers", results["pitchers"])):
        ids_all = set(df.loc[df["opp_hand"] == "all", "player_id"])
        ids_R = set(df.loc[df["opp_hand"] == "R", "player_id"])
        ids_L = set(df.loc[df["opp_hand"] == "L", "player_id"])
        missing_from_all = (ids_R | ids_L) - ids_all
        assert not missing_from_all, (
            f"{role}: {len(missing_from_all)} player_ids appear in vs_R or "
            f"vs_L but not in all — sample: {sorted(missing_from_all)[:5]}"
        )
