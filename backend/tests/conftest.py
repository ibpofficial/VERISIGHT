import pytest
from backend.app.core.init_db import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initializes schema and seeds test users before running test session."""
    init_db()

