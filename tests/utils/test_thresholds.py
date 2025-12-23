"""Tests for threshold utilities."""

import pytest

from savant_api_extractor.utils.extraction_type import ExtractionType
from savant_api_extractor.utils.thresholds import (
    DEFAULT_MIN_PAS_BATTER,
    DEFAULT_MIN_PAS_PITCHER,
    OPEN_MIN_PAS_BATTER,
    OPEN_MIN_PAS_PITCHER,
    SPRING_TRAINING_MIN_PAS_BATTER,
    SPRING_TRAINING_MIN_PAS_PITCHER,
    ThresholdType,
    WIDE_MIN_PAS_BATTER,
    WIDE_MIN_PAS_PITCHER,
    get_min_pas,
)


@pytest.mark.parametrize(
    ("threshold_type", "player_type", "expected"),
    [
        (ThresholdType.DEFAULT, ExtractionType.BATTER, str(DEFAULT_MIN_PAS_BATTER)),
        (ThresholdType.DEFAULT, ExtractionType.PITCHER, str(DEFAULT_MIN_PAS_PITCHER)),
        (ThresholdType.WIDE, ExtractionType.BATTER, str(WIDE_MIN_PAS_BATTER)),
        (ThresholdType.WIDE, ExtractionType.PITCHER, str(WIDE_MIN_PAS_PITCHER)),
        (ThresholdType.OPEN, ExtractionType.BATTER, str(OPEN_MIN_PAS_BATTER)),
        (ThresholdType.OPEN, ExtractionType.PITCHER, str(OPEN_MIN_PAS_PITCHER)),
        (
            ThresholdType.SPRING_TRAINING,
            ExtractionType.BATTER,
            str(SPRING_TRAINING_MIN_PAS_BATTER),
        ),
        (
            ThresholdType.SPRING_TRAINING,
            ExtractionType.PITCHER,
            str(SPRING_TRAINING_MIN_PAS_PITCHER),
        ),
    ],
)
def test_get_min_pas(
    threshold_type: ThresholdType,
    player_type: ExtractionType,
    expected: str,
) -> None:
    assert get_min_pas(threshold_type, player_type) == expected
