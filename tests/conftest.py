from collections.abc import Callable
from pathlib import Path

import pytest

@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def load_fixture(fixtures_dir: Path) -> Callable[[str], str]:
    """Factory fixture to load fixture files."""
    def _load(filename: str) -> str:
        return (fixtures_dir / filename).read_text()
    return _load

@pytest.fixture
def batters_fixture(load_fixture: Callable[[str], str]) -> str:
    """Load the batters fixture."""
    return load_fixture("batters_fixture.txt")

@pytest.fixture
def pitchers_fixture(load_fixture: Callable[[str], str]) -> str:
    """Load the pitchers fixture."""
    return load_fixture("pitchers_fixture.txt")
