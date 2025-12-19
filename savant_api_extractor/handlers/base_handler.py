"""Base handler for Savant API data extraction."""

from abc import ABC
import pandas as pd

from savant_api_extractor.utils.logger import Logger


class BaseHandler(ABC):
    """Base class for all data handlers."""

    BASE_URL = "https://baseballsavant.mlb.com/statcast_search/csv?"

    def __init__(self, name: str) -> None:
        """
        Initialize the base handler.

        Args:
            name: Name of the handler (for logging)
        """
        self.logger = Logger(f"{__name__}.{name}")
        self.name = name

    def clean_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean CSV headers by removing whitespace and converting to lowercase.

        Args:
            df: DataFrame with raw headers

        Returns:
            DataFrame with cleaned headers
        """
        self.logger.info("Cleaning CSV headers")
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        return df
