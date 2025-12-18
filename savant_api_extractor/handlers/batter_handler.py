"""Handler for extracting batter statistics from Savant API."""

import io
from typing import Any

import pandas as pd
import requests

from savant_api_extractor.handlers.base_handler import BaseHandler


class BatterHandler(BaseHandler):
    """Handler for extracting batter statistics."""

    BASE_URL = "https://baseballsavant.mlb.com/statcast_search/csv?"

    def __init__(self) -> None:
        """Initialize the batter handler."""
        super().__init__("BatterHandler")

    def extract(self, query_params: dict[str, Any]) -> pd.DataFrame:
        """
        Extract batter statistics from the Savant API.

        Args:
            query_params: Query parameters for the API request

        Returns:
            DataFrame with cleaned batter statistics
        """
        self.logger.info("Extracting batter statistics")
        self.logger.debug(f"Query params: {query_params}")

        try:
            # Make API request
            response = requests.get(self.BASE_URL, params=query_params, timeout=30)
            response.raise_for_status()

            # Read CSV from response
            df = pd.read_csv(
                io.StringIO(response.text),
                low_memory=False,
            )

            self.logger.info(f"Retrieved {len(df)} rows of batter data")

            # Clean headers
            df = self.clean_headers(df)

            return df

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching batter data: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error processing batter data: {e}")
            raise
