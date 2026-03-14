import sqlite3
import os
from contextlib import contextmanager

# Place the database file at the project root, one level above this package.
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "queue_system.db",
)


@contextmanager
def connect():
    """Opens a connection to queue_system.db and ensures it is closed on exit."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


def create_tables():
    """Creates the customers table if it doesn't already exist."""
    with connect() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket     TEXT      NOT NULL,
                name       TEXT      NOT NULL,
                status     TEXT      NOT NULL DEFAULT 'waiting',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
