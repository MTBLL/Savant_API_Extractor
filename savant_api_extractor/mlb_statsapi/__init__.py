"""MLB StatsAPI integrations — sibling to the Savant client.

This package wraps the official MLB Stats API (`statsapi.mlb.com`) which is
public, no auth required. It lives alongside the Savant code because both
feed the same analytics pipeline; both are RT-fetch from the analytics
app's perspective.

Currently exposes:

- `fetch_probable_pitchers(date)` — daily probable pitchers per game.
"""

from __future__ import annotations

from savant_api_extractor.mlb_statsapi.probable_pitchers import (
    fetch_probable_pitchers,
)

__all__ = ["fetch_probable_pitchers"]
