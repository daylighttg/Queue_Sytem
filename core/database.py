import sqlite3
import os

# Place the database file at the project root, one level above this package.
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "queue_system.db",
)


def connect():
    """Opens a connection to queue_system.db (creates the file if it doesn't exist)."""
    return sqlite3.connect(DB_PATH)


def create_tables():
    """Creates the customers and counters tables if they don't already exist."""
    conn = connect()
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS counters (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT    NOT NULL
        )
    """)

    conn.commit()
    conn.close()
