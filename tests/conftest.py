from pathlib import Path
import pytest

@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def load_fixture(fixtures_dir):
    """Factory fixture to load fixture files."""
    def _load(filename):
        return (fixtures_dir / filename).read_text()
    return _load

@pytest.fixture
def batters_fixture(load_fixture):
    """Load the batters fixture."""
    return load_fixture("batters_fixture.txt")

@pytest.fixture
def pitchers_fixture(load_fixture):
    """Load the pitchers fixture."""
    return load_fixture("pitchers_fixture.txt")