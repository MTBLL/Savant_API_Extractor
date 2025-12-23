"""Tests for the SavantRunner class."""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from savant_api_extractor.runner.savant_runner import SavantRunner
from savant_api_extractor.utils.extraction_type import ExtractionType
from savant_api_extractor.utils.thresholds import ThresholdType


def test_runner_initialization(tmp_path: Path) -> None:
    runner = SavantRunner(
        season="2025",
        extraction_type="batter",
        threshold_type=ThresholdType.DEFAULT,
        output_dir=tmp_path,
        output_filename="runner_output",
    )

    assert runner.extraction_method == ExtractionType.BATTER
    assert runner.threshold_type == ThresholdType.DEFAULT
    assert runner.season == "2025"
    assert runner.output_dir == tmp_path
    assert runner.filename == "runner_output"


def test_runner_export_to_json_dataframe(
    tmp_path: Path,
    batters_fixture: str,
) -> None:
    runner = SavantRunner(
        season="2025",
        extraction_type="batter",
        output_dir=tmp_path,
        output_filename="batters_export",
    )
    df = pd.read_csv(io.StringIO(batters_fixture), low_memory=False)

    output_path = runner._export_to_json(df)  # pyright: ignore[reportPrivateUsage]

    assert output_path == tmp_path / "batters_export.json"
    data = json.loads(output_path.read_text(encoding="utf-8"))
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
        extraction_type="batter",
        output_dir=tmp_path,
        output_filename="batter_stats",
    )

    with patch("savant_api_extractor.handlers.base_handler.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = batters_fixture
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        results = runner.run()

    assert mock_get.call_count == 1
    assert list(results.keys()) == ["batters"]
    assert results["batters"].iloc[0]["name"] == "Judge, Aaron"

    output_path = tmp_path / "batter_stats.json"
    assert output_path.exists()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert "batters" in data
    assert data["batters"][0]["name"] == "Judge, Aaron"


def test_runner_run_all_exports_json(
    tmp_path: Path,
    batters_fixture: str,
    pitchers_fixture: str,
) -> None:
    runner = SavantRunner(
        season="2025",
        extraction_type="all",
        output_dir=tmp_path,
        output_filename="all_stats",
    )

    with patch("savant_api_extractor.handlers.base_handler.requests.get") as mock_get:
        batter_response = MagicMock()
        batter_response.text = batters_fixture
        batter_response.raise_for_status = MagicMock()
        pitcher_response = MagicMock()
        pitcher_response.text = pitchers_fixture
        pitcher_response.raise_for_status = MagicMock()
        mock_get.side_effect = [batter_response, pitcher_response]

        results = runner.run()

    assert mock_get.call_count == 2
    assert "batters" in results
    assert "pitchers" in results
    assert results["batters"].iloc[0]["name"] == "Judge, Aaron"
    assert results["pitchers"].iloc[0]["name"] == "Marinaccio, Ron"

    output_path = tmp_path / "all_stats.json"
    assert output_path.exists()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert "batters" in data
    assert "pitchers" in data
    assert len(data["batters"]) > 0
    assert len(data["pitchers"]) > 0
    assert data["batters"][0]["name"] == "Judge, Aaron"
    assert data["pitchers"][0]["name"] == "Marinaccio, Ron"
