"""Handler for extracting batter statistics from Savant API."""

import io
from typing import Any

import pandas as pd
import requests

from savant_api_extractor.handlers.base_handler import BaseHandler
from savant_api_extractor.utils import BATTER_HEADER_MAPPINGS


class BatterHandler(BaseHandler):
    """Handler for extracting batter statistics."""

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
            response = requests.get(super().BASE_URL, params=query_params, timeout=30)
            response.raise_for_status()

            # Read CSV from response
            df = pd.read_csv(
                io.StringIO(response.text),
                low_memory=False,
            )

            self.logger.info(f"Retrieved {len(df)} rows of batter data")

            # Clean headers
            df = df.rename(columns=BATTER_HEADER_MAPPINGS)

            return df

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching batter data: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error processing batter data: {e}")
            raise
