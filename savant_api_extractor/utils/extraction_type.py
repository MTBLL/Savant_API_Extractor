"""Extraction type enum used by runner and controller."""

from enum import Enum


class ExtractionType(str, Enum):
    BATTER = "batters"
    PITCHER = "pitchers"
    ALL = "all"
