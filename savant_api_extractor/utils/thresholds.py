"""Threshold options for query parameter generation."""

from enum import Enum
from typing import Final


class ThresholdType(str, Enum):
    """Threshold types for minimum plate appearances."""

    DEFAULT = "default"
    WIDE = "wide"
    OPEN = "open"
    SPRING_TRAINING = "spring_training"


# Default minimum plate appearances
DEFAULT_MIN_PAS_BATTER: Final[int] = 30
DEFAULT_MIN_PAS_PITCHER: Final[int] = 20

# Wide threshold (50% of default)
WIDE_MIN_PAS_BATTER: Final[int] = 15
WIDE_MIN_PAS_PITCHER: Final[int] = 10

# Open threshold (no minimums)
OPEN_MIN_PAS_BATTER: Final[int] = 0
OPEN_MIN_PAS_PITCHER: Final[int] = 0

# Spring training (no minimums)
SPRING_TRAINING_MIN_PAS_BATTER: Final[int] = 0
SPRING_TRAINING_MIN_PAS_PITCHER: Final[int] = 0


def get_min_pas(threshold_type: ThresholdType, player_type: str) -> str:
    """
    Get minimum plate appearances based on threshold type and player type.

    Args:
        threshold_type: The threshold type to use
        player_type: "batter" or "pitcher"

    Returns:
        Minimum plate appearances value
    """
    min_pas: str = ""

    match threshold_type:
        case ThresholdType.DEFAULT:
            min_pas = (
                str(DEFAULT_MIN_PAS_BATTER)
                if player_type == "batter"
                else str(DEFAULT_MIN_PAS_PITCHER)
            )
        case ThresholdType.WIDE:
            min_pas = (
                str(WIDE_MIN_PAS_BATTER)
                if player_type == "batter"
                else str(WIDE_MIN_PAS_PITCHER)
            )
        case ThresholdType.OPEN:
            min_pas = (
                str(OPEN_MIN_PAS_BATTER)
                if player_type == "batter"
                else str(OPEN_MIN_PAS_PITCHER)
            )
        case ThresholdType.SPRING_TRAINING:
            min_pas = (
                str(SPRING_TRAINING_MIN_PAS_BATTER)
                if player_type == "batter"
                else str(SPRING_TRAINING_MIN_PAS_PITCHER)
            )

    return min_pas
