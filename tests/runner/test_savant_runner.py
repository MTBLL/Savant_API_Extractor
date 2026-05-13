"""Tests for the SavantRunner class."""

import io
import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from savant_api_extractor.runner.savant_runner import SavantRunner
from savant_api_extractor.utils.extraction_type import ExtractionType
from savant_api_extractor.utils.thresholds import ThresholdType


def test_runner_initialization(tmp_path: Path) -> None:
    runner = SavantRunner(
        season="2025",
        extraction_type="batters",
        threshold_type=ThresholdType.DEFAULT,
        output_dir=tmp_path,
    )

    assert runner.extraction_method == ExtractionType.BATTER
    assert runner.threshold_type == ThresholdType.DEFAULT
    assert runner.season == "2025"
    assert runner.output_dir == tmp_path


def test_runner_export_to_json_dataframe(
    tmp_path: Path,
    batters_fixture: str,
) -> None:
    runner = SavantRunner(
        season="2025",
        extraction_type="batters",
        output_dir=tmp_path,
    )
    df = pd.read_csv(io.StringIO(batters_fixture), low_memory=False)

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
    assert data[0]["player_name"] == "Judge, Aaron"
    assert data[0]["player_id"] == 592450


def test_runner_run_batter_returns_dict(
    tmp_path: Path,
    batters_fixture: str,
) -> None:
    runner = SavantRunner(
        season="2025",
        extraction_type="batters",
        output_dir=tmp_path,
    )

    with patch("savant_api_extractor.handlers.base_handler.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = batters_fixture
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        results = runner.run()

    # 3 calls per player_type: overall + vs RHP + vs LHP
    assert mock_get.call_count == 3
    assert list(results.keys()) == ["batters"]
    assert set(results["batters"]["opp_hand"].unique()) == {"all", "R", "L"}
    assert results["batters"].iloc[0]["name"] == "Judge, Aaron"

    # Find the file matching pattern: savant_batters_YYYY_MM_DD_HHMM.json
    output_files = list(tmp_path.glob("savant_batters_*.json"))
    assert len(output_files) == 1
    assert re.match(
        r"savant_batters_\d{4}_\d{2}_\d{2}_\d{4}\.json", output_files[0].name
    )

    data = json.loads(output_files[0].read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert data[0]["name"] == "Judge, Aaron"
    assert data[0]["player_type"] == "batter"
    assert "opp_hand" in data[0]
    # Percentile-rank columns are no longer emitted at extract time.
    assert not any(k.endswith("_pct_rnk") for k in data[0].keys())
    assert {row["opp_hand"] for row in data} == {"all", "R", "L"}


def test_runner_run_all_exports_json(
    tmp_path: Path,
    batters_fixture: str,
    pitchers_fixture: str,
) -> None:
    runner = SavantRunner(
        season="2025",
        extraction_type="all",
        output_dir=tmp_path,
    )

    with patch("savant_api_extractor.handlers.base_handler.requests.get") as mock_get:
        def make_response(text: str) -> MagicMock:
            r = MagicMock()
            r.text = text
            r.raise_for_status = MagicMock()
            return r

        # 3 batter calls (all/R/L) then 3 pitcher calls (all/R/L)
        mock_get.side_effect = [
            make_response(batters_fixture),
            make_response(batters_fixture),
            make_response(batters_fixture),
            make_response(pitchers_fixture),
            make_response(pitchers_fixture),
            make_response(pitchers_fixture),
        ]

        results = runner.run()

    assert mock_get.call_count == 6
    assert "batters" in results
    assert "pitchers" in results
    assert set(results["batters"]["opp_hand"].unique()) == {"all", "R", "L"}
    assert set(results["pitchers"]["opp_hand"].unique()) == {"all", "R", "L"}
    assert results["batters"].iloc[0]["name"] == "Judge, Aaron"
    assert results["pitchers"].iloc[0]["name"] == "Marinaccio, Ron"

    # Find files matching pattern: savant_{batters|pitchers}_YYYY_MM_DD_HHMM.json
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
    assert batters_data[0]["name"] == "Judge, Aaron"
    assert batters_data[0]["player_type"] == "batter"
    assert pitchers_data[0]["name"] == "Marinaccio, Ron"
    assert pitchers_data[0]["player_type"] == "pitcher"
    # Percentile-rank columns are no longer emitted at extract time.
    assert not any(k.endswith("_pct_rnk") for k in batters_data[0].keys())
    assert not any(k.endswith("_pct_rnk") for k in pitchers_data[0].keys())
