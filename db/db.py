from db.orm_models import (
    Base,
    Game,
    GameLength,
    Genre,
    Publisher,
    GameGenre,
    GamePublisher,
)
from sqlalchemy import create_engine, text, inspect, delete, select, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from contextlib import contextmanager
import os
import time

load_dotenv()

DB_URL = os.environ["DB_URL"]  # env variable, URL to database

# map from postgres table name to ORM model
TABLE_MAP = {
    "games": Game,
    "game_lengths": GameLength,
    "genres": Genre,
    "publishers": Publisher,
    "game_genres": GameGenre,
    "game_publishers": GamePublisher,
}

engine = create_engine(DB_URL, echo=False, pool_pre_ping=True)


def retry_conn(num_retries: int):
    """
    Decorator that retries a function on database connection failure.

    Args:
        num_retries: Number of times to retry before giving up.

    Raises:
        Exception: If max retries are reached without a successful connection.
    """

    def decorator_retry_func(func):
        def wrapper_retry_func(*args, **kwargs):

            for retry in range(num_retries):
                try:
                    func(*args, **kwargs)
                    break
                except OperationalError:
                    if retry == num_retries - 1:
                        raise Exception("Max retries reached!")
                    print(
                        f"Failed attempt #{retry + 1} to connect to DB. Retrying connection..."
                    )
                    time.sleep(3)

        return wrapper_retry_func

    return decorator_retry_func


class Database:
    """
    Handles all database connections and operations.

    Manages the SQLAlchemy engine and session factory.
    Provides methods for schema management and query execution.
    """

    def __init__(self):
        self.name = engine.url.database
        self.Session = sessionmaker(engine)

    def get_inspector(self):
        """Returns a SQLAlchemy inspector instance for the current engine."""

        return inspect(engine)

    def get_session(self):
        """Returns a new SQLAlchemy session instance."""
        return self.Session()

    @contextmanager
    def transaction(self):
        """Context manager that handles session lifecycle, commit, and error handling."""
        try:
            with self.get_session() as session:
                yield session
                session.commit()
        except OperationalError:
            print("Could not connect to db. Is Docker running?")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def get_db_status(self, verbose: bool):
        """
        Checks if the database is reachable.

        Returns:
            bool: True if connected, False if not

        Args:
            verbose: bool, specified if detailed db output needed.

        Raises:
            Exception: If unsuccessful connection, raise OperationalError
        """

        db_dict = {}
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

                if verbose:
                    result = conn.execute(
                        text("""
                                SELECT 
                                current_database(),
                                version(),
                                pg_size_pretty(pg_database_size(current_database())),
                                (SELECT count(*) from pg_stat_activity WHERE datname = current_database());
                                """)
                    )

                    rows = result.fetchall()

                    db_dict["db_name"] = rows[0][0]
                    version_split = rows[0][1].split()
                    db_dict["db_version"] = (
                        version_split[0] + " " + version_split[1]
                    )  # only extract database type and version
                    db_dict["db_size"] = rows[0][
                        2
                    ]  # size of db (kB, MB, GB, or TB, etc)
                    db_dict["db_num_connections"] = rows[0][3]
                    db_dict["tables"] = self.get_inspector().get_table_names()

            return True, db_dict
        except OperationalError:
            return False, db_dict

    def create_schema(self):
        """Creates all database tables defined in the ORM models."""

        try:
            Base.metadata.create_all(engine)
            print("Schema created!")

        except OperationalError:
            print("Could not connect to db. Is Docker running?")

    def delete_schema(self):
        """Deletes all database tables defined in the ORM models."""

        try:
            Base.metadata.drop_all(engine)
            print("Schema deleted!")
        except OperationalError:
            print("Could not connect to db. Is Docker running?")

    def get_dependent_tables(self, table):
        """Returns a list of tables that have foreign keys referencing the given table."""
        inspector = self.get_inspector()
        affected = []

        for t in Base.metadata.tables.keys():
            fks = inspector.get_foreign_keys(t)
            for fk in fks:
                if fk["referred_table"] == table:
                    affected.append(t)

        return affected

    def _delete_table(self, session, table):
        """private method to delete the contents of a table."""
        if table in TABLE_MAP:
            session.execute(
                delete(TABLE_MAP[table]),
                execution_options={"synchronize_session": False},
            )
        else:
            raise ValueError(f"Unknown table '{table}'")

    def truncate_table(self, table):
        """truncates a specified table"""
        table = table.strip().lower()
        with self.transaction() as session:
            self._delete_table(session, table)
            print(f"Table '{table}' truncated successfully!")

    def truncate_all(self):
        """Truncates all tables in correct dependency order."""
        with self.transaction() as session:
            for table in reversed(Base.metadata.sorted_tables):
                self._delete_table(session, table.name)
            print("All tables truncated successfully!")

    def get_table_count(self, table):
        """Returns the row count for a specified table."""
        table = table.strip().lower()
        with self.transaction() as session:
            if table in TABLE_MAP:
                return session.scalar(
                    select(func.count()).select_from(TABLE_MAP[table])
                )
            else:
                raise ValueError(f"Unknown table '{table}'")

    def get_all_cols(self, table, limit_cnt):
        """Returns the row count for a specified table."""

        if limit_cnt == 0 or limit_cnt is None:
            limit_cnt = 5

        table = table.strip().lower()
        with self.transaction() as session:
            if table in TABLE_MAP:
                table_obj = Base.metadata.tables[table]
                results = (
                    session.execute(select(table_obj).limit(limit_cnt)).mappings().all()
                )
                return [dict(row) for row in results]

            else:
                raise ValueError(f"Unknown table '{table}'")
