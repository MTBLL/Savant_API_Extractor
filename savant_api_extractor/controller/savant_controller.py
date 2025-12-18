"""Controller for managing data extraction from Savant API."""

from typing import Any

import pandas as pd

from savant_api_extractor.handlers.batter_handler import BatterHandler
from savant_api_extractor.handlers.pitcher_handler import PitcherHandler
from savant_api_extractor.utils.logger import Logger


class SavantController:
    """Controller that interfaces with handlers to extract data."""

    def __init__(self) -> None:
        """Initialize the controller with handlers."""
        self.logger = Logger(f"{__name__}.SavantController")
        self.batter_handler = BatterHandler()
        self.pitcher_handler = PitcherHandler()
        self.logger.info("Controller initialized")

    def extract_batters(self, query_params: dict[str, Any]) -> pd.DataFrame:
        """
        Extract batter statistics.

        Args:
            query_params: Query parameters for the API request

        Returns:
            DataFrame with batter statistics
        """
        self.logger.info("Extracting batter statistics")
        return self.batter_handler.extract(query_params)

    def extract_pitchers(self, query_params: dict[str, Any]) -> pd.DataFrame:
        """
        Extract pitcher statistics.

        Args:
            query_params: Query parameters for the API request

        Returns:
            DataFrame with pitcher statistics
        """
        self.logger.info("Extracting pitcher statistics")
        return self.pitcher_handler.extract(query_params)

    def extract_all(
        self,
        batter_params: dict[str, Any] | None = None,
        pitcher_params: dict[str, Any] | None = None,
    ) -> dict[str, pd.DataFrame]:
        """
        Extract both batter and pitcher statistics.

        Args:
            batter_params: Query parameters for batters (optional)
            pitcher_params: Query parameters for pitchers (optional)

        Returns:
            Dictionary with 'batters' and 'pitchers' DataFrames
        """
        self.logger.info("Extracting all statistics")
        results: dict[str, pd.DataFrame] = {}

        if batter_params:
            results["batters"] = self.extract_batters(batter_params)

        if pitcher_params:
            results["pitchers"] = self.extract_pitchers(pitcher_params)

        return results
