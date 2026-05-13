"""Shared pytest fixtures for the Savant_API_Extractor test suite.

Fixture files mirror the actual API calls made by the runner: 6 HTTP calls
per extraction (2 roles x 3 handedness splits), so we keep 6 CSV files
under `tests/fixtures/{role}/{opp_hand}.csv` — one fixture per call.

For handler-level and controller-level tests (which exercise a single
HTTP call), use the per-split fixtures directly (e.g. `batters_all_fixture`).
For runner-level tests (which orchestrate all 3 splits per role), use the
`*_split_fixtures` dicts and feed them to `mock_get.side_effect` in the
order the runner makes the calls: all → R → L.
"""

from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture(fixtures_dir: Path) -> Callable[[str], str]:
    """Factory fixture to load fixture files by relative path."""

    def _load(rel_path: str) -> str:
        return (fixtures_dir / rel_path).read_text()

    return _load


# Per-call fixtures — one per HTTP request the extractor actually makes.
@pytest.fixture
def batters_all_fixture(load_fixture: Callable[[str], str]) -> str:
    """Batter season totals (opp_hand='all', min_pas=30)."""
    return load_fixture("batters/all.csv")


@pytest.fixture
def batters_vs_R_fixture(load_fixture: Callable[[str], str]) -> str:
    """Batter stats vs RHP (opp_hand='R', no min_pas threshold)."""
    return load_fixture("batters/vs_R.csv")


@pytest.fixture
def batters_vs_L_fixture(load_fixture: Callable[[str], str]) -> str:
    """Batter stats vs LHP (opp_hand='L', no min_pas threshold)."""
    return load_fixture("batters/vs_L.csv")


@pytest.fixture
def pitchers_all_fixture(load_fixture: Callable[[str], str]) -> str:
    """Pitcher season totals (opp_hand='all', min_pas=30)."""
    return load_fixture("pitchers/all.csv")


@pytest.fixture
def pitchers_vs_R_fixture(load_fixture: Callable[[str], str]) -> str:
    """Pitcher stats vs RHB (opp_hand='R', no min_pas threshold)."""
    return load_fixture("pitchers/vs_R.csv")


@pytest.fixture
def pitchers_vs_L_fixture(load_fixture: Callable[[str], str]) -> str:
    """Pitcher stats vs LHB (opp_hand='L', no min_pas threshold)."""
    return load_fixture("pitchers/vs_L.csv")


# Aggregate dicts ordered to match `OPP_HAND_SPLITS = ("all", "R", "L")`.
# Use `list(batters_split_fixtures.values())` as `mock_get.side_effect` to
# feed the runner's 3 batter calls in the correct sequence.
@pytest.fixture
def batters_split_fixtures(
    batters_all_fixture: str,
    batters_vs_R_fixture: str,
    batters_vs_L_fixture: str,
) -> dict[str, str]:
    return {
        "all": batters_all_fixture,
        "R": batters_vs_R_fixture,
        "L": batters_vs_L_fixture,
    }


@pytest.fixture
def pitchers_split_fixtures(
    pitchers_all_fixture: str,
    pitchers_vs_R_fixture: str,
    pitchers_vs_L_fixture: str,
) -> dict[str, str]:
    return {
        "all": pitchers_all_fixture,
        "R": pitchers_vs_R_fixture,
        "L": pitchers_vs_L_fixture,
    }
