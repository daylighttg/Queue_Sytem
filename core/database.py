"""Database and persistence helpers for the Queue System."""

from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator, Sequence

from .exceptions import DatabaseError

LOGGER = logging.getLogger(__name__)

DEFAULT_DB_FILENAME = "queue_system.db"
SQLITE_TIMEOUT_SECONDS = 5.0
EMPTY_TICKET_VALUE = ""

SQL_CREATE_CUSTOMERS_TABLE = """
CREATE TABLE IF NOT EXISTS customers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket     TEXT      NOT NULL,
    name       TEXT      NOT NULL,
    status     TEXT      NOT NULL DEFAULT 'waiting',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""
SQL_INSERT_CUSTOMER = "INSERT INTO customers (ticket, name, status) VALUES (?, ?, ?)"
SQL_UPDATE_TICKET = "UPDATE customers SET ticket = ? WHERE id = ?"
SQL_SELECT_FIRST_BY_STATUS = (
    "SELECT id, ticket, name FROM customers WHERE status = ? ORDER BY id ASC LIMIT 1"
)
SQL_SELECT_EXISTS_BY_STATUS = "SELECT 1 FROM customers WHERE status = ? LIMIT 1"
SQL_UPDATE_STATUS = "UPDATE customers SET status = ? WHERE id = ?"
SQL_SELECT_WAITING = (
    "SELECT ticket, name, created_at FROM customers WHERE status = ? ORDER BY id ASC"
)
SQL_SELECT_SERVING = (
    "SELECT ticket, name FROM customers WHERE status = ? ORDER BY id ASC LIMIT 1"
)
SQL_SELECT_HISTORY = "SELECT ticket, name, status, created_at FROM customers ORDER BY id ASC"
SQL_SELECT_ALL_RECORDS = "SELECT id, ticket, name, status FROM customers ORDER BY id ASC"
SQL_SELECT_COUNT_BY_STATUS = "SELECT COUNT(*) FROM customers WHERE status = ?"
SQL_SELECT_STATUS_COUNTS = "SELECT status, COUNT(*) FROM customers GROUP BY status"
SQL_SELECT_ID_BY_TICKET = "SELECT id FROM customers WHERE ticket = ?"
SQL_SELECT_COUNT_WAITING_BEFORE = (
    "SELECT COUNT(*) FROM customers WHERE status = ? AND id < ?"
)
SQL_SELECT_RECORD_BY_ID = "SELECT ticket, name FROM customers WHERE id = ?"
SQL_DELETE_RECORD_BY_ID = "DELETE FROM customers WHERE id = ?"
SQL_SELECT_TOTAL_RECORDS = "SELECT COUNT(*) FROM customers"
SQL_DELETE_ALL_RECORDS = "DELETE FROM customers"
SQL_SELECT_WAITING_NAME_EXISTS = (
    "SELECT 1 FROM customers WHERE name = ? AND status = ? LIMIT 1"
)

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    DEFAULT_DB_FILENAME,
)

SQLParameters = Sequence[Any]


def _validate_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise DatabaseError(f"{field_name} must be a string.")
    normalized_value = value.strip()
    if not normalized_value:
        raise DatabaseError(f"{field_name} cannot be empty.")
    return normalized_value


def _validate_positive_integer(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DatabaseError(f"{field_name} must be an integer.")
    if value <= 0:
        raise DatabaseError(f"{field_name} must be greater than zero.")
    return value


def _as_parameters(parameters: SQLParameters) -> tuple[Any, ...]:
    return tuple(parameters)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection and always close it.

    Yields:
        sqlite3.Connection: Active SQLite connection.

    Raises:
        DatabaseError: If the connection cannot be created or used.
    """
    database_path = _validate_non_empty_string(DB_PATH, "DB_PATH")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(
            database_path,
            check_same_thread=False,
            timeout=SQLITE_TIMEOUT_SECONDS,
        )
        yield connection
    except sqlite3.Error as db_error:
        raise DatabaseError(f"Database operation failed: {db_error}") from db_error
    finally:
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error as close_error:
                LOGGER.exception("Failed to close database connection: %s", close_error)


class QueueRepository:
    """Persistence gateway for queue operations backed by SQLite."""

    @staticmethod
    def _fetch_one(
        query: str,
        parameters: SQLParameters = (),
    ) -> tuple[Any, ...] | None:
        with connect() as connection:
            cursor = connection.cursor()
            cursor.execute(query, _as_parameters(parameters))
            return cursor.fetchone()

    @staticmethod
    def _fetch_all(query: str, parameters: SQLParameters = ()) -> list[tuple[Any, ...]]:
        with connect() as connection:
            cursor = connection.cursor()
            cursor.execute(query, _as_parameters(parameters))
            return cursor.fetchall()

    @staticmethod
    def _execute_write(query: str, parameters: SQLParameters = ()) -> int:
        with connect() as connection:
            cursor = connection.cursor()
            cursor.execute(query, _as_parameters(parameters))
            connection.commit()
            return cursor.rowcount

    def create_tables(self) -> None:
        """Create required database tables if they do not exist."""
        with connect() as connection:
            cursor = connection.cursor()
            cursor.execute(SQL_CREATE_CUSTOMERS_TABLE)
            connection.commit()

    def enqueue_customer(
        self,
        customer_name: str,
        waiting_status: str,
        ticket_prefix: str,
        ticket_width: int,
    ) -> str:
        """Insert a waiting customer and generate a ticket.

        Args:
            customer_name: Customer display name.
            waiting_status: Status value used for waiting customers.
            ticket_prefix: Prefix used in generated ticket values.
            ticket_width: Width for zero-padded ticket numeric part.

        Returns:
            Generated ticket value.
        """
        normalized_name = _validate_non_empty_string(customer_name, "customer_name")
        normalized_status = _validate_non_empty_string(waiting_status, "waiting_status")
        normalized_prefix = _validate_non_empty_string(ticket_prefix, "ticket_prefix")
        validated_width = _validate_positive_integer(ticket_width, "ticket_width")

        with connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                SQL_INSERT_CUSTOMER,
                (EMPTY_TICKET_VALUE, normalized_name, normalized_status),
            )
            customer_id = cursor.lastrowid
            if customer_id is None:
                raise DatabaseError("Failed to create customer record.")

            generated_ticket = f"{normalized_prefix}{customer_id:0{validated_width}d}"
            cursor.execute(SQL_UPDATE_TICKET, (generated_ticket, customer_id))
            connection.commit()

        return generated_ticket

    def get_first_by_status(self, status: str) -> tuple[int, str, str] | None:
        """Return the earliest customer matching a status."""
        normalized_status = _validate_non_empty_string(status, "status")
        row = self._fetch_one(SQL_SELECT_FIRST_BY_STATUS, (normalized_status,))
        if row is None:
            return None
        return int(row[0]), str(row[1]), str(row[2])

    def any_with_status(self, status: str) -> bool:
        """Return whether at least one customer exists with a status."""
        normalized_status = _validate_non_empty_string(status, "status")
        return self._fetch_one(SQL_SELECT_EXISTS_BY_STATUS, (normalized_status,)) is not None

    def update_status(self, customer_id: int, status: str) -> None:
        """Update a customer's status."""
        validated_customer_id = _validate_positive_integer(customer_id, "customer_id")
        normalized_status = _validate_non_empty_string(status, "status")
        self._execute_write(SQL_UPDATE_STATUS, (normalized_status, validated_customer_id))

    def list_waiting(self, waiting_status: str) -> list[tuple[str, str, str]]:
        """Return waiting rows as (ticket, name, created_at)."""
        normalized_status = _validate_non_empty_string(waiting_status, "waiting_status")
        rows = self._fetch_all(SQL_SELECT_WAITING, (normalized_status,))
        return [(str(ticket), str(name), str(created_at)) for ticket, name, created_at in rows]

    def get_serving(self, serving_status: str) -> tuple[str, str] | None:
        """Return the currently serving row as (ticket, name), if any."""
        normalized_status = _validate_non_empty_string(serving_status, "serving_status")
        row = self._fetch_one(SQL_SELECT_SERVING, (normalized_status,))
        if row is None:
            return None
        return str(row[0]), str(row[1])

    def list_history(self) -> list[tuple[str, str, str, str]]:
        """Return history rows as (ticket, name, status, created_at)."""
        rows = self._fetch_all(SQL_SELECT_HISTORY)
        return [
            (str(ticket), str(name), str(status), str(created_at))
            for ticket, name, status, created_at in rows
        ]

    def list_all_records(self) -> list[tuple[int, str, str, str]]:
        """Return all rows as (id, ticket, name, status)."""
        rows = self._fetch_all(SQL_SELECT_ALL_RECORDS)
        return [
            (int(record_id), str(ticket), str(name), str(status))
            for record_id, ticket, name, status in rows
        ]

    def count_by_status(self, status: str) -> int:
        """Return count of rows for a given status."""
        normalized_status = _validate_non_empty_string(status, "status")
        row = self._fetch_one(SQL_SELECT_COUNT_BY_STATUS, (normalized_status,))
        if row is None:
            return 0
        return int(row[0])

    def status_counts(self) -> list[tuple[str, int]]:
        """Return grouped counts as (status, count)."""
        rows = self._fetch_all(SQL_SELECT_STATUS_COUNTS)
        return [(str(status), int(total)) for status, total in rows]

    def customer_id_by_ticket(self, ticket: str) -> int | None:
        """Return customer id by ticket, or None when absent."""
        normalized_ticket = _validate_non_empty_string(ticket, "ticket")
        row = self._fetch_one(SQL_SELECT_ID_BY_TICKET, (normalized_ticket,))
        if row is None:
            return None
        return int(row[0])

    def count_waiting_before(self, customer_id: int, waiting_status: str) -> int:
        """Return number of waiting customers ahead of a customer id."""
        validated_customer_id = _validate_positive_integer(customer_id, "customer_id")
        normalized_status = _validate_non_empty_string(waiting_status, "waiting_status")
        row = self._fetch_one(
            SQL_SELECT_COUNT_WAITING_BEFORE,
            (normalized_status, validated_customer_id),
        )
        if row is None:
            return 0
        return int(row[0])

    def record_by_id(self, record_id: int) -> tuple[str, str] | None:
        """Return (ticket, name) for a record id, or None when absent."""
        validated_record_id = _validate_positive_integer(record_id, "record_id")
        row = self._fetch_one(SQL_SELECT_RECORD_BY_ID, (validated_record_id,))
        if row is None:
            return None
        return str(row[0]), str(row[1])

    def delete_by_id(self, record_id: int) -> None:
        """Delete a single record by id."""
        validated_record_id = _validate_positive_integer(record_id, "record_id")
        self._execute_write(SQL_DELETE_RECORD_BY_ID, (validated_record_id,))

    def count_records(self) -> int:
        """Return total number of customer records."""
        row = self._fetch_one(SQL_SELECT_TOTAL_RECORDS)
        if row is None:
            return 0
        return int(row[0])

    def clear_all_records(self) -> None:
        """Delete every customer record."""
        self._execute_write(SQL_DELETE_ALL_RECORDS)

    def exists_waiting_name(self, customer_name: str, waiting_status: str) -> bool:
        """Return whether a customer name is already waiting in the queue."""
        normalized_name = _validate_non_empty_string(customer_name, "customer_name")
        normalized_status = _validate_non_empty_string(waiting_status, "waiting_status")
        return (
            self._fetch_one(
                SQL_SELECT_WAITING_NAME_EXISTS,
                (normalized_name, normalized_status),
            )
            is not None
        )


_QUEUE_REPOSITORY = QueueRepository()


def get_repository() -> QueueRepository:
    """Return the default queue repository instance."""
    return _QUEUE_REPOSITORY


def create_tables() -> None:
    """Create database tables needed by the application."""
    _QUEUE_REPOSITORY.create_tables()
