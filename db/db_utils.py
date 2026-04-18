from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
import os
import time
from db.models import Base


load_dotenv()

DB_URL = os.environ["DB_URL"]


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
        self.engine = create_engine(f"{DB_URL}", echo=True)

    @retry_conn(num_retries=3)
    def execute_sql(self, sql):
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()

    def create_schema(self):
        """
        Creates all database tables defined in the ORM models.

        Raises:
            OperationalError: If the database is unreachable.
        """

        try:
            Base.metadata.create_all(self.engine)
            print("Schema created!")

        except OperationalError:
            print("Could not connect to db. Is Docker running?")

    def delete_schema(self):
        """
        Deletes all database tables defined in the ORM models.

        Raises:
            OperationalError: If the database is unreachable.
        """

        try:
            Base.metadata.drop_all(self.engine)
            print("Schema deleted!")
        except OperationalError:
            print("Could not connect to db. Is Docker running?")
