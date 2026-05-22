"""Round-half-up rounding for exported floats.

Python's built-in `round()` uses banker's rounding (round-half-to-even):
`round(2.5)` is `2`, `round(0.125, 2)` is `0.12`. Exported stats should
round half *up* consistently, so this module rounds via `decimal.Decimal`
with `ROUND_HALF_UP` — ties go away from zero (`2.5` -> `3`, `-2.5` -> `-3`).

This module imports pandas, so it is NOT re-exported from
`utils/__init__.py`; import the full path.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from functools import partial

import pandas as pd

EXPORT_PRECISION = 3


def round_half_up(value: float, places: int = EXPORT_PRECISION) -> float:
    """Round `value` half-up to `places` decimal places.

    NaN and infinity pass through untouched. `Decimal(str(value))` is used
    so the float's binary-representation noise doesn't tip a half-way value
    the wrong way — `Decimal(0.125)` carries that noise, `Decimal("0.125")`
    does not.
    """
    if math.isnan(value) or math.isinf(value):
        return value
    quantum = Decimal(1).scaleb(-places)  # e.g. places=3 -> Decimal("0.001")
    return float(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP))


def round_float_columns(
    df: pd.DataFrame, places: int = EXPORT_PRECISION
) -> pd.DataFrame:
    """Return a copy of `df` with every float column rounded half-up.

    Only float-dtyped columns are touched — integer identity columns
    (`player_id`, `year`, `team_id`, ...) and object columns are left
    exactly as-is. The input frame is not mutated.
    """
    df = df.copy()
    rounder = partial(round_half_up, places=places)
    for col in df.select_dtypes(include="float").columns:
        df[col] = df[col].map(rounder)
    return df
