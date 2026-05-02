from src.db.db import Database

db = Database()

def get_db():
    """Provides a database session for route handlers."""
    with db.get_session() as session:
        yield session