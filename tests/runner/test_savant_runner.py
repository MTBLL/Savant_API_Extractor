"""Tests for the SavantRunner class."""

import io
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from savant_api_extractor.leaderboards import ETL_TIER_CONFIGS
from savant_api_extractor.runner.savant_runner import (
    SavantRunner,
    _route_std_log_handlers_through_live,
)
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
    """Runner makes 3 HTTP calls for the batter splits and concats them."""
    runner = SavantRunner(
        season="2026",
        extraction_type="batters",
        output_dir=tmp_path,
        include_leaderboards=False,  # focus this test on splits behavior
    )

    # Fetches run through a thread pool now — route by URL rather than
    # relying on a fixed call order.
    router = _build_url_router(
        splits_fixtures={"batter": batters_split_fixtures},
        leaderboard_fixtures={},
    )
    with patch(
        "savant_api_extractor.handlers.base_handler.requests.get",
        side_effect=router,
    ) as mock_get:
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

    # Fetches run through a thread pool now — route by URL rather than
    # relying on a fixed call order.
    router = _build_url_router(
        splits_fixtures={
            "batter": batters_split_fixtures,
            "pitcher": pitchers_split_fixtures,
        },
        leaderboard_fixtures={},
    )
    with patch(
        "savant_api_extractor.handlers.base_handler.requests.get",
        side_effect=router,
    ) as mock_get:
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
    rolling_html_fixture: str,
) -> None:
    """End-to-end: splits + one call per ETL config + rolling, one file per result."""
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

    # RollingHandler uses its own requests.get (not base_handler's), so the
    # URL router doesn't cover it — patch its HTML fetch directly.
    with patch(
        "savant_api_extractor.handlers.base_handler.requests.get",
        side_effect=router,
    ) as mock_get, patch.object(
        runner.rolling_handler, "_fetch_html", return_value=rolling_html_fixture
    ):
        results = runner.run()

    # 6 split calls + one call per ETL-tier config. (expected_statistics_batter
    # is intentionally not an ETL config — its columns live in the batter
    # splits export — so the count tracks len(ETL_TIER_CONFIGS).) Rolling is
    # patched at _fetch_html, so it doesn't add to base_handler's mock_get.
    assert mock_get.call_count == 6 + len(ETL_TIER_CONFIGS)

    # Results dict has 2 split keys + one key per ETL-tier config + rolling
    expected_keys = (
        {"batters", "pitchers", "rolling"} | {c.name for c in ETL_TIER_CONFIGS}
    )
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

    # Rolling is long-format on (cat, cat_bin) — all 6 categories present
    rolling_file = next(tmp_path.glob("savant_rolling_*.json"))
    rolling_rows = json.loads(rolling_file.read_text())
    assert {(r["cat"], r["cat_bin"]) for r in rolling_rows} == {
        ("Batter", "50"),
        ("Batter", "100"),
        ("Batter", "250"),
        ("Pitcher", "50"),
        ("Pitcher", "100"),
        ("Pitcher", "250"),
    }


def test_runner_leaderboard_failure_logs_and_reraises(
    tmp_path: Path,
    batters_split_fixtures: dict[str, str],
    pitchers_split_fixtures: dict[str, str],
    rolling_html_fixture: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When a leaderboard pull fails, the runner logs which one failed and re-raises.

    Exercises the exception path of the flat fetch pool in `run()` (the
    `try/except` around `future.result()`). The split calls succeed normally;
    the leaderboard handler is patched to raise, simulating a Savant outage /
    parse failure for a leaderboard.
    """
    runner = SavantRunner(
        season="2026",
        extraction_type="all",
        output_dir=tmp_path,
        include_leaderboards=True,
    )

    # Splits route by URL; leaderboard calls never reach requests.get because
    # leaderboard_handler.extract is patched to raise before it gets there.
    router = _build_url_router(
        splits_fixtures={
            "batter": batters_split_fixtures,
            "pitcher": pitchers_split_fixtures,
        },
        leaderboard_fixtures={},
    )
    with patch(
        "savant_api_extractor.handlers.base_handler.requests.get",
        side_effect=router,
    ), patch.object(
        runner.leaderboard_handler,
        "extract",
        side_effect=RuntimeError("simulated leaderboard failure"),
    ), patch.object(
        runner.rolling_handler, "_fetch_html", return_value=rolling_html_fixture
    ):
        with pytest.raises(RuntimeError, match="simulated leaderboard failure"):
            runner.run()

    # The runner logged which fetch failed before re-raising.
    assert any(
        "Fetch failed [leaderboard" in record.message
        and "simulated leaderboard failure" in record.message
        for record in caplog.records
    ), f"expected failure log line; got records: {[r.message for r in caplog.records]}"


def test_runner_split_failure_logs_and_reraises(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When a statcast_search split fetch fails, the runner logs which split
    failed and re-raises.

    Mirror of the leaderboard-failure test for the other branch of the flat
    fetch pool's exception handler — here the controller (splits) is patched
    to raise. `include_leaderboards=False` keeps the pool to just the 3 split
    fetches, so the split-failure path is the only one that can fire.
    """
    runner = SavantRunner(
        season="2026",
        extraction_type="batters",
        output_dir=tmp_path,
        include_leaderboards=False,
    )

    with patch.object(
        runner.controller,
        "extract",
        side_effect=RuntimeError("simulated split failure"),
    ):
        with pytest.raises(RuntimeError, match="simulated split failure"):
            runner.run()

    # The runner logged which split failed before re-raising.
    assert any(
        "Fetch failed [split batters/" in record.message
        and "simulated split failure" in record.message
        for record in caplog.records
    ), f"expected split failure log line; got records: {[r.message for r in caplog.records]}"


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
    router = _build_url_router(
        splits_fixtures={
            "batter": batters_split_fixtures,
            "pitcher": pitchers_split_fixtures,
        },
        leaderboard_fixtures={},
    )
    with patch(
        "savant_api_extractor.handlers.base_handler.requests.get",
        side_effect=router,
    ):
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


class TestRouteStdLogHandlersThroughLive:
    """Coverage for the log-stream rewiring helper used inside the Live block."""

    def test_stdout_handler_repointed_and_stderr_left_on_stderr(self):
        """An stdout-bound handler should move to the current sys.stdout
        and an stderr-bound handler to the current sys.stderr. Both must
        be restored on exit."""
        stdout_handler = logging.StreamHandler(sys.__stdout__)
        stderr_handler = logging.StreamHandler(sys.__stderr__)
        other_stream = io.StringIO()
        other_handler = logging.StreamHandler(other_stream)
        try:
            lg = logging.getLogger("savant.tests.route_helper")
            lg.addHandler(stdout_handler)
            lg.addHandler(stderr_handler)
            lg.addHandler(other_handler)

            fake_stdout = io.StringIO()
            fake_stderr = io.StringIO()
            saved_out, saved_err = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = fake_stdout, fake_stderr
            try:
                with _route_std_log_handlers_through_live():
                    assert stdout_handler.stream is fake_stdout
                    assert stderr_handler.stream is fake_stderr
                    # Streams not matching __stdout__ / __stderr__ must
                    # be untouched.
                    assert other_handler.stream is other_stream
            finally:
                sys.stdout, sys.stderr = saved_out, saved_err

            # Restored on exit.
            assert stdout_handler.stream is sys.__stdout__
            assert stderr_handler.stream is sys.__stderr__
            assert other_handler.stream is other_stream
        finally:
            lg = logging.getLogger("savant.tests.route_helper")
            for h in (stdout_handler, stderr_handler, other_handler):
                lg.removeHandler(h)

    def test_host_wrapped_stdout_handler_repointed(self):
        """A handler bound to a host-wrapped sys.stdout (Jupyter / pytest
        capture style) is not sys.__stdout__, yet must still be repointed
        once rich.live.Live wraps that host stream in a FileProxy."""
        from rich.console import Console
        from rich.file_proxy import FileProxy

        host_stdout = io.StringIO()  # what a host (e.g. pytest) installed
        handler = logging.StreamHandler(host_stdout)
        logger_name = "savant.tests.route_helper.wrapped"
        try:
            lg = logging.getLogger(logger_name)
            lg.addHandler(handler)

            # Live wraps the host stream; sys.stdout is now a FileProxy
            # whose rich_proxied_file is the original host stream.
            live_stdout = FileProxy(Console(file=io.StringIO()), host_stdout)
            saved_out = sys.stdout
            sys.stdout = live_stdout
            try:
                with _route_std_log_handlers_through_live():
                    assert handler.stream is live_stdout
            finally:
                sys.stdout = saved_out

            # Restored to the host stream on exit.
            assert handler.stream is host_stdout
        finally:
            logging.getLogger(logger_name).removeHandler(handler)
