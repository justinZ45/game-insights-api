import pytest
from src.db.db import Database


def test_db_init_defaults(monkeypatch):
    """Database should fall back to env variables or hardcoded defaults."""
    # Mock environment variables to ensure predictable test behavior
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_pass")
    monkeypatch.setenv("DB_HOST", "test_host")
    monkeypatch.setenv("DB_PORT", "9999")
    monkeypatch.setenv("DB_NAME", "test_db")
    # Make sure DB_URL is cleared so it doesn't bypass component building
    monkeypatch.delenv("DB_URL", raising=False)

    db = Database()
    
    assert db.host == "test_host"
    assert str(db.port) == "9999"
    assert db.user == "test_user"
    assert db.name == "test_db"


def test_db_init_with_cli_overrides(monkeypatch):
    """Database constructor overrides should completely supersede env variables."""
    monkeypatch.setenv("DB_USER", "env_user")
    monkeypatch.setenv("DB_HOST", "env_host")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "env_db")
    monkeypatch.delenv("DB_URL", raising=False)

    # Instantiate with explicit overrides
    db = Database(
        host="override_host", 
        port=1234, 
        user="override_user", 
        db_name="override_db"
    )
    
    assert db.host == "override_host"
    assert str(db.port) == "1234"
    assert db.user == "override_user"
    assert db.name == "override_db"


def test_db_init_prioritizes_db_url(monkeypatch):
    """If DB_URL is present and no overrides are passed, it should be used directly."""
    target_url = "postgresql://url_user:url_pass@url_host:8888/url_db"
    monkeypatch.setenv("DB_URL", target_url)
    
    db = Database()
    
    assert db.host == "url_host"
    assert str(db.port) == "8888"
    assert db.user == "url_user"
    assert db.name == "url_db"


@pytest.mark.integration
def test_db_conn():
    """Verify database connection. Requires running Docker container with Postgres."""
    db = Database()

    status, _ = db.get_db_status(False)
    assert status is True
