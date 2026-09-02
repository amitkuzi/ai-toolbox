"""Pytest configuration and shared fixtures for AI Toolbox tests"""
import pytest
import tempfile
from pathlib import Path
import sys

# Add scripts directory to Python path
scripts_dir = Path(__file__).parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_dir():
    """Temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "adversary: mark test as requiring LLM APIs (Kimi-K3, Claude)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (>1s)"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on location"""
    for item in items:
        # Mark adversary tests
        if "adversary" in item.nodeid:
            item.add_marker(pytest.mark.adversary)

        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
