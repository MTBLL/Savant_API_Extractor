"""Tests for the handler classes."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from savant_api_extractor.handlers import BatterHandler, PitcherHandler


class TestBatterHandler:
    """Test cases for the BatterHandler class."""

    def test_batter_handler_initialization(self) -> None:
        """Test that BatterHandler can be initialized."""
        handler = BatterHandler()
        assert handler.name == "BatterHandler"
        assert handler.logger is not None

    @patch("savant_api_extractor.handlers.batter_handler.requests.get")
    def test_batter_handler_extract(
        self, mock_get: MagicMock, batters_all_fixture: str
    ) -> None:
        """Test that BatterHandler parses an opp_hand='all' fixture correctly."""
        mock_response = MagicMock()
        mock_response.text = batters_all_fixture
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        handler = BatterHandler()
        query_params = {"all": "true", "type": "details"}
        df = handler.extract(query_params)

        # Shape + schema
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "player_name" not in df.columns  # raw col renamed to "name"
        for col in ("name", "player_id", "first_name", "last_name", "name_ascii", "slug"):
            assert col in df.columns

        # Identity column ordering (name → first_name → last_name → name_ascii → slug)
        columns = df.columns.to_list()
        name_index = columns.index("name")
        assert columns[name_index + 1 : name_index + 5] == [
            "first_name",
            "last_name",
            "name_ascii",
            "slug",
        ]

        # Role tagging applied to every row
        assert (df["player_type"] == "batter").all()

        # Percentile-rank columns are no longer emitted at extract time.
        assert not any(col.endswith("_pct_rnk") for col in df.columns)

        # Anchor on Ohtani — present across all batter splits, name-parser-stable.
        ohtani = df.loc[df["name"] == "Ohtani, Shohei"].iloc[0]
        assert ohtani["first_name"] == "Shohei"
        assert ohtani["last_name"] == "Ohtani"
        assert ohtani["name_ascii"] == "Shohei Ohtani"
        assert ohtani["slug"] == "shohei-ohtani"
        assert ohtani["player_type"] == "batter"
        # 2026 season-to-date Ohtani stats (regenerated from fixture)
        assert ohtani["hardhit_pct"] == pytest.approx(46.2962962962963)
        assert ohtani["barrels_per_bbe_pct"] == pytest.approx(16.666666666666664)
        assert ohtani["barrels_per_pa_pct"] == pytest.approx(9.72972972972973)

        mock_get.assert_called_once()

    @patch("savant_api_extractor.handlers.pitcher_handler.requests.get")
    def test_batter_handler_request_exception(self, mock_get: MagicMock) -> None:
        """Test that BatterHandler raises RequestException on network errors."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        handler = BatterHandler()
        query_params = {"all": "true", "type": "details"}

        with pytest.raises(requests.exceptions.ConnectionError):
            handler.extract(query_params)


class TestPitcherHandler:
    """Test cases for the PitcherHandler class."""

    def test_pitcher_handler_initialization(self) -> None:
        """Test that PitcherHandler can be initialized."""
        handler = PitcherHandler()
        assert handler.name == "PitcherHandler"
        assert handler.logger is not None

    @patch("savant_api_extractor.handlers.pitcher_handler.requests.get")
    def test_pitcher_handler_extract(
        self, mock_get: MagicMock, pitchers_all_fixture: str
    ) -> None:
        """Test that PitcherHandler parses an opp_hand='all' fixture correctly."""
        mock_response = MagicMock()
        mock_response.text = pitchers_all_fixture
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        handler = PitcherHandler()
        query_params = {"all": "true", "type": "details"}
        df = handler.extract(query_params)

        # Shape + schema
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "player_name" not in df.columns
        for col in ("name", "player_id", "first_name", "last_name", "name_ascii", "slug"):
            assert col in df.columns

        columns = df.columns.to_list()
        name_index = columns.index("name")
        assert columns[name_index + 1 : name_index + 5] == [
            "first_name",
            "last_name",
            "name_ascii",
            "slug",
        ]

        # Role tagging
        assert (df["player_type"] == "pitcher").all()

        # Percentile-rank columns are no longer emitted at extract time.
        assert not any(col.endswith("_pct_rnk") for col in df.columns)

        # Anchor on Ohtani — two-way player, present in pitcher fixtures too.
        ohtani = df.loc[df["name"] == "Ohtani, Shohei"].iloc[0]
        assert ohtani["first_name"] == "Shohei"
        assert ohtani["last_name"] == "Ohtani"
        assert ohtani["name_ascii"] == "Shohei Ohtani"
        assert ohtani["slug"] == "shohei-ohtani"
        assert ohtani["player_type"] == "pitcher"
        # 2026 season-to-date Ohtani pitcher stats (regenerated from fixture)
        assert ohtani["hardhit_pct"] == pytest.approx(38.46153846153847)
        assert ohtani["barrels_per_bbe_pct"] == pytest.approx(3.296703296703297)
        assert ohtani["barrels_per_pa_pct"] == pytest.approx(2.068965517241379)

        mock_get.assert_called_once()

    @patch("savant_api_extractor.handlers.pitcher_handler.requests.get")
    def test_pitcher_handler_request_exception(self, mock_get: MagicMock) -> None:
        """Test that PitcherHandler raises RequestException on network errors."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        handler = PitcherHandler()
        query_params = {"all": "true", "type": "details"}

        with pytest.raises(requests.exceptions.ConnectionError):
            handler.extract(query_params)

    @patch("savant_api_extractor.handlers.pitcher_handler.requests.get")
    def test_pitcher_handler_http_error(self, mock_get: MagicMock) -> None:
        """Test that PitcherHandler raises HTTPError on HTTP errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        handler = PitcherHandler()
        query_params = {"all": "true", "type": "details"}

        with pytest.raises(requests.exceptions.HTTPError):
            handler.extract(query_params)

    @patch("savant_api_extractor.handlers.pitcher_handler.requests.get")
    @patch("savant_api_extractor.handlers.pitcher_handler.pd.read_csv")
    def test_pitcher_handler_processing_exception(
        self, mock_read_csv: MagicMock, mock_get: MagicMock
    ) -> None:
        """Test that PitcherHandler raises Exception on processing errors."""
        mock_response = MagicMock()
        mock_response.text = "invalid csv data"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        mock_read_csv.side_effect = ValueError("Invalid CSV format")

        handler = PitcherHandler()
        query_params = {"all": "true", "type": "details"}

        with pytest.raises(ValueError, match="Invalid CSV format"):
            handler.extract(query_params)
