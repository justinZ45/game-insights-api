import pytest
from src.db.db import Database


@pytest.mark.integration
def test_db_conn():
    """Verify database connection. Requires running Docker container with Postgres."""
    db = Database()

    status, _ = db.get_db_status(False)
    assert status is True
