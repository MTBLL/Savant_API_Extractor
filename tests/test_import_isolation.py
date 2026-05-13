"""Regression tests for the package's lazy-import boundary.

These run in a *fresh subprocess* per test so they observe `sys.modules`
without contamination from any prior test in this suite (where the
LeaderboardHandler and runner tests pull pandas in long before these
tests would run). In-process checks would always show pandas loaded.

The contract being pinned here: which sub-import paths are "light" (no
pandas/numpy) vs. "heavy" (load the DataFrame stack). The README's
import-map table in "Using as a library" makes promises that match the
assertions here — if these tests start failing, either the assertions
need updating or someone re-introduced an eager pandas trigger.
"""

from __future__ import annotations

import subprocess
import sys


def _run_import_probe(import_stmt: str) -> dict:
    """Execute `import_stmt` in a clean subprocess and report sys.modules state.

    Returns a dict with:
      - `returncode`: subprocess exit code (0 if the script ran cleanly)
      - `pandas_loaded`: bool
      - `numpy_loaded`: bool
      - `savant_modules`: sorted list of savant_api_extractor.* modules loaded
      - `stderr`: subprocess stderr (for debugging if the import fails)
    """
    probe = f"""
import sys, json
{import_stmt}
report = {{
    'pandas_loaded': 'pandas' in sys.modules,
    'numpy_loaded':  'numpy'  in sys.modules,
    'savant_modules': sorted(
        m for m in sys.modules if m.startswith('savant_api_extractor')
    ),
}}
print(json.dumps(report))
"""
    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode != 0:
        return {"returncode": result.returncode, "stderr": result.stderr}

    import json

    payload = json.loads(result.stdout.strip().split("\n")[-1])
    payload["returncode"] = 0
    payload["stderr"] = result.stderr
    return payload


def test_mlb_statsapi_import_does_not_load_pandas_or_numpy() -> None:
    """`from savant_api_extractor.mlb_statsapi import fetch_probable_pitchers`
    must stay lightweight — no pandas, no numpy, no Savant handlers.

    If this regresses, the analytics app pays a multi-hundred-MB import cost
    every time it fetches probable pitchers. The README's import-map table
    documents this as a "No pandas/numpy" path.
    """
    result = _run_import_probe(
        "from savant_api_extractor.mlb_statsapi import fetch_probable_pitchers"
    )
    assert result["returncode"] == 0, f"import failed:\n{result.get('stderr')}"
    assert not result["pandas_loaded"], (
        "pandas leaked into the mlb_statsapi import path — check that "
        "utils/__init__.py doesn't re-export anything pandas-dependent. "
        f"loaded savant modules: {result['savant_modules']}"
    )
    assert not result["numpy_loaded"], "numpy leaked into mlb_statsapi imports"

    # Lightweight import path shouldn't touch the DataFrame-shaped
    # subpackages either — those exist for the bulk runner / handlers, not
    # for the StatsAPI use case.
    forbidden_prefixes = (
        "savant_api_extractor.handlers",
        "savant_api_extractor.runner",
        "savant_api_extractor.controller",
        "savant_api_extractor.leaderboards",
    )
    leaked = [
        m
        for m in result["savant_modules"]
        if any(m.startswith(p) for p in forbidden_prefixes)
    ]
    assert not leaked, f"heavy subpackages leaked into mlb_statsapi import: {leaked}"


def test_leaderboard_handler_import_loads_pandas_as_expected() -> None:
    """LeaderboardHandler is documented as a "loads pandas" path —
    sanity-check that's still true (catches the inverse regression where
    we accidentally make it ultra-lazy and break a downstream caller that
    expects pandas to be available immediately after import)."""
    result = _run_import_probe(
        "from savant_api_extractor.handlers import LeaderboardHandler"
    )
    assert result["returncode"] == 0, f"import failed:\n{result.get('stderr')}"
    assert result["pandas_loaded"], (
        "LeaderboardHandler import no longer loads pandas — the README's "
        "import-map promises it does. If lazy-loading was intentional, "
        "update the import-map table."
    )
