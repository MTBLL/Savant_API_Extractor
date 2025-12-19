"""Base handler for Savant API data extraction."""

from abc import ABC
import io
from typing import Any, Dict
import pandas as pd
import requests

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

    def get_dataframe(self, query_params: Dict[str, Any]) -> pd.DataFrame:
        self.logger.debug(f"Query params: {query_params}")
        # Make API request
        response = requests.get(self.BASE_URL, params=query_params, timeout=30)
        response.raise_for_status()

        # Read CSV from response
        df = pd.read_csv(
            io.StringIO(response.text),
            low_memory=False,
        )

        return df
