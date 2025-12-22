"""Extraction type enum used by runner and controller."""

from enum import Enum


class ExtractionType(str, Enum):
    BATTER = "batter"
    PITCHER = "pitcher"
    ALL = "all"
