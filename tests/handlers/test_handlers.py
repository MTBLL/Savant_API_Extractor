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
    def test_batter_handler_extract(self, mock_get: MagicMock, batters_fixture: str) -> None:
        """Test that BatterHandler can extract data using fixture file."""
        # Read fixture file
        mock_response = MagicMock()
        mock_response.text = batters_fixture
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        handler = BatterHandler()
        query_params = {"all": "true", "type": "details"}
        df = handler.extract(query_params)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        
        # Assert on first couple of items
        # Note: headers are cleaned (lowercase, spaces -> underscores)
        first_row = df.iloc[0]
        assert "name" in df.columns  # "player_name" becomes "name" after cleaning
        assert "player_id" in df.columns
        assert first_row["name"] == "Judge, Aaron"
        assert first_row["player_id"] == 592450
        
        # Check second row
        if len(df) > 1:
            second_row = df.iloc[1]
            assert second_row["name"] == "Jensen, Carter"
            assert second_row["player_id"] == 695600
        
        mock_get.assert_called_once()

    @patch("savant_api_extractor.handlers.pitcher_handler.requests.get")
    def test_batter_handler_request_exception(self, mock_get: MagicMock) -> None:
        """Test that PitcherHandler raises RequestException on network errors."""
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
    def test_pitcher_handler_extract(self, mock_get: MagicMock, pitchers_fixture: str) -> None:
        """Test that PitcherHandler can extract data."""
        # Mock CSV response
        mock_response = MagicMock()
        mock_response.text = pitchers_fixture
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        handler = PitcherHandler()
        query_params = {"all": "true", "type": "details"}
        df = handler.extract(query_params)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0 
        assert "player_name" not in df.columns
        assert "name" in df.columns
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
