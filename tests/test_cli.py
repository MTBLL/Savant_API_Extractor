"""Tests for the CLI entry point."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from savant_api_extractor.__main__ import main
from savant_api_extractor.utils.thresholds import ThresholdType


def test_cli_defaults_to_current_year() -> None:
    runner = CliRunner()

    with (
        patch("savant_api_extractor.__main__.datetime") as mock_datetime,
        patch("savant_api_extractor.__main__.SavantRunner") as mock_runner_class,
    ):
        mock_datetime.now.return_value.year = 2026

        result = runner.invoke(main, [])

    assert result.exit_code == 0
    mock_runner_class.assert_called_once_with(
        "2026",
        "all",
        ThresholdType.DEFAULT,
        output_dir=Path("."),
    )
    mock_runner_class.return_value.run.assert_called_once_with()


def test_cli_uses_explicit_season() -> None:
    runner = CliRunner()

    with patch("savant_api_extractor.__main__.SavantRunner") as mock_runner_class:
        result = runner.invoke(main, ["--season", "2025"])

    assert result.exit_code == 0
    mock_runner_class.assert_called_once_with(
        "2025",
        "all",
        ThresholdType.DEFAULT,
        output_dir=Path("."),
    )
    mock_runner_class.return_value.run.assert_called_once_with()
