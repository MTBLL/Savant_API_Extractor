"""Tests for the handler classes."""

from unittest.mock import MagicMock, patch

import pandas as pd

from savant_api_extractor.handlers import BatterHandler, PitcherHandler


class TestBatterHandler:
    """Test cases for the BatterHandler class."""

    def test_batter_handler_initialization(self) -> None:
        """Test that BatterHandler can be initialized."""
        handler = BatterHandler()
        assert handler.name == "BatterHandler"
        assert handler.logger is not None

    @patch("savant_api_extractor.handlers.batter_handler.requests.get")
    def test_batter_handler_extract(self, mock_get: MagicMock) -> None:
        """Test that BatterHandler can extract data."""
        # Mock CSV response
        csv_data = "col1,col2\nvalue1,value2\nvalue3,value4"
        mock_response = MagicMock()
        mock_response.text = csv_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        handler = BatterHandler()
        query_params = {"all": "true", "type": "details"}
        df = handler.extract(query_params)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "col1" in df.columns
        mock_get.assert_called_once()

    def test_clean_headers(self) -> None:
        """Test that headers are cleaned properly."""
        handler = BatterHandler()
        df = pd.DataFrame({"Col 1": [1, 2], "Col 2": [3, 4]})
        cleaned_df = handler.clean_headers(df)
        
        assert "col_1" in cleaned_df.columns
        assert "col_2" in cleaned_df.columns


class TestPitcherHandler:
    """Test cases for the PitcherHandler class."""

    def test_pitcher_handler_initialization(self) -> None:
        """Test that PitcherHandler can be initialized."""
        handler = PitcherHandler()
        assert handler.name == "PitcherHandler"
        assert handler.logger is not None

    @patch("savant_api_extractor.handlers.pitcher_handler.requests.get")
    def test_pitcher_handler_extract(self, mock_get: MagicMock) -> None:
        """Test that PitcherHandler can extract data."""
        # Mock CSV response
        csv_data = "col1,col2\nvalue1,value2\nvalue3,value4"
        mock_response = MagicMock()
        mock_response.text = csv_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        handler = PitcherHandler()
        query_params = {"all": "true", "type": "details"}
        df = handler.extract(query_params)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "col1" in df.columns
        mock_get.assert_called_once()
