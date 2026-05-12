"""Controller for managing data extraction from Savant API."""

import pandas as pd

from savant_api_extractor.handlers.batter_handler import BatterHandler
from savant_api_extractor.handlers.base_handler import BaseHandler
from savant_api_extractor.handlers.pitcher_handler import PitcherHandler
from savant_api_extractor.utils.extraction_type import ExtractionType
from savant_api_extractor.utils.logger import Logger
from savant_api_extractor.utils.query_params import (
    BATTER_STANDS,
    FLAG_COMPETITIVE,
    FLAG_NOT_BUNT,
    GAME_TYPE_REGULAR,
    GAME_TYPE_SPRING_TRAINING,
    GROUP_BY,
    GROUP_BY_NAME,
    HF_FLAG,
    HF_GAME_TYPE,
    HF_SEASON,
    MIN_PLATE_APPEARANCES,
    PITCHER_THROWS,
    SORT_COL_XWOBA,
    SORT_COLUMN,
    SORT_ORDER,
    SORT_ORDER_ASC,
    SORT_ORDER_DESC,
)
from savant_api_extractor.utils.thresholds import ThresholdType, get_min_pas

OPP_HAND_OVERALL: str = "all"
OPP_HAND_R: str = "R"
OPP_HAND_L: str = "L"
OPP_HAND_SPLITS: tuple[str, ...] = (OPP_HAND_OVERALL, OPP_HAND_R, OPP_HAND_L)


class SavantController:
    """Controller that interfaces with handlers to extract data."""

    def __init__(self, threshold_type: ThresholdType) -> None:
        """Initialize the controller with handlers."""
        self.logger: Logger = Logger(f"{__name__}.SavantController")
        self.batter_handler: BatterHandler = BatterHandler()
        self.pitcher_handler: PitcherHandler = PitcherHandler()
        self.logger.info("Controller initialized")
        self.threshold_type: ThresholdType = threshold_type

    def _generate_query_params(
        self,
        player_type: ExtractionType,
        season: str,
        opp_hand: str = OPP_HAND_OVERALL,
    ) -> dict[str, str]:
        """
        Generate query parameters based on options.

        Args:
            player_type: "batters" or "pitchers"
            season: Season year (e.g., "2025").
            opp_hand: Opposing-side handedness split. "all" (default) returns
                full-season stats subject to the configured min_pas threshold.
                "R" or "L" filters to PAs against right/left-handed opponents
                and drops the min_pas threshold per the splits policy.

        Returns:
            Dictionary of query parameters
        """
        player_type_param = {
            ExtractionType.BATTER: "batter",
            ExtractionType.PITCHER: "pitcher",
        }.get(player_type)

        assert player_type_param is not None, f"Unsupported player type: {player_type}"

        params: dict[str, str] = {
            "player_type": player_type_param,
            HF_GAME_TYPE: (
                GAME_TYPE_SPRING_TRAINING
                if self.threshold_type == ThresholdType.SPRING_TRAINING
                else GAME_TYPE_REGULAR
            ),
            GROUP_BY: GROUP_BY_NAME,
            SORT_COLUMN: SORT_COL_XWOBA,
            SORT_ORDER: (
                SORT_ORDER_ASC
                if player_type == ExtractionType.PITCHER
                else SORT_ORDER_DESC
            ),
            HF_FLAG: f"{FLAG_NOT_BUNT}|{FLAG_COMPETITIVE}|",
            HF_SEASON: season,
        }

        if opp_hand == OPP_HAND_OVERALL:
            min_pas = get_min_pas(self.threshold_type, player_type)
            params[MIN_PLATE_APPEARANCES] = min_pas
        elif opp_hand in (OPP_HAND_R, OPP_HAND_L):
            split_param = (
                PITCHER_THROWS
                if player_type == ExtractionType.BATTER
                else BATTER_STANDS
            )
            params[split_param] = opp_hand
        else:
            raise ValueError(f"Unsupported opp_hand: {opp_hand!r}")

        self.logger.debug(
            (
                f"Generated {player_type} query params with "
                f"threshold={self.threshold_type.value}, "
                f"opp_hand={opp_hand}"
            )
        )

        return params

    def extract(
        self,
        player_type: ExtractionType,
        season: str,
        opp_hand: str = OPP_HAND_OVERALL,
    ) -> pd.DataFrame:
        """
        Extract player statistics for a single handedness split.

        Args:
            player_type: "batters" or "pitchers"
            season: Season year (e.g., "2025").
            opp_hand: "all" for overall (threshold-gated) stats, "R" or "L" for
                vs-RHP/vs-LHP (batters) or vs-RHB/vs-LHB (pitchers).

        Returns:
            DataFrame with player statistics, tagged with an opp_hand column.
        """
        handler: BaseHandler
        match player_type:
            case ExtractionType.BATTER:
                handler = self.batter_handler
            case ExtractionType.PITCHER:
                handler = self.pitcher_handler
            case _:
                raise ValueError(f"Unsupported player type: {player_type}")

        self.logger.info(f"Extracting player statistics (opp_hand={opp_hand})")
        query_params = self._generate_query_params(player_type, season, opp_hand)
        return handler.extract(query_params, opp_hand=opp_hand)
