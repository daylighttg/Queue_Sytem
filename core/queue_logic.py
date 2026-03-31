"""Business logic layer for the Queue System."""

from __future__ import annotations

from typing import Protocol

from .database import get_repository
from .exceptions import QueueError, QueueFullError

WAITING_STATUS = "waiting"
SERVING_STATUS = "serving"
DONE_STATUS = "done"
TOTAL_KEY = "total"
TICKET_PREFIX = "Q"
TICKET_NUMBER_WIDTH = 3
ALLOW_DUPLICATE_WAITING_NAMES = True
ALREADY_SERVING_MESSAGE = "A customer is already being served. Mark them as done first."

WaitingRow = tuple[str, str, str]
ServingRow = tuple[str, str]
HistoryRow = tuple[str, str, str, str]
RecordRow = tuple[int, str, str, str]


class QueueRepositoryProtocol(Protocol):
    """Protocol for queue persistence used by QueueService."""

    def enqueue_customer(
        self,
        customer_name: str,
        waiting_status: str,
        ticket_prefix: str,
        ticket_width: int,
    ) -> str:
        """Insert a customer and return generated ticket."""

    def get_first_by_status(self, status: str) -> tuple[int, str, str] | None:
        """Return first customer by status."""

    def any_with_status(self, status: str) -> bool:
        """Return whether any customer has the status."""

    def update_status(self, customer_id: int, status: str) -> None:
        """Update status for a customer id."""

    def list_waiting(self, waiting_status: str) -> list[WaitingRow]:
        """Return waiting rows."""

    def get_serving(self, serving_status: str) -> ServingRow | None:
        """Return currently serving row."""

    def list_history(self) -> list[HistoryRow]:
        """Return full history rows."""

    def list_all_records(self) -> list[RecordRow]:
        """Return all records."""

    def count_by_status(self, status: str) -> int:
        """Return number of rows by status."""

    def status_counts(self) -> list[tuple[str, int]]:
        """Return grouped status counts."""

    def customer_id_by_ticket(self, ticket: str) -> int | None:
        """Return customer id by ticket."""

    def count_waiting_before(self, customer_id: int, waiting_status: str) -> int:
        """Return number of waiting customers ahead of id."""

    def record_by_id(self, record_id: int) -> tuple[str, str] | None:
        """Return (ticket, name) for record id."""

    def delete_by_id(self, record_id: int) -> None:
        """Delete a record by id."""

    def count_records(self) -> int:
        """Return total row count."""

    def clear_all_records(self) -> None:
        """Delete all queue records."""

    def exists_waiting_name(self, customer_name: str, waiting_status: str) -> bool:
        """Return whether a waiting record with name exists."""


class QueueService:
    """Facade for queue business operations."""

    def __init__(
        self,
        repository: QueueRepositoryProtocol | None = None,
        *,
        allow_duplicate_waiting_names: bool = ALLOW_DUPLICATE_WAITING_NAMES,
    ) -> None:
        """Initialize a queue service instance.

        Args:
            repository: Persistence implementation. Defaults to SQLite repository.
            allow_duplicate_waiting_names: Whether repeated waiting names are allowed.
        """
        self._repository: QueueRepositoryProtocol = (
            repository if repository is not None else get_repository()
        )
        self._allow_duplicate_waiting_names = allow_duplicate_waiting_names

    @staticmethod
    def _validate_name(customer_name: str) -> str:
        if not isinstance(customer_name, str):
            raise QueueError("Customer name must be a string.")
        normalized_name = customer_name.strip()
        if not normalized_name:
            raise QueueError("Customer name cannot be empty.")
        return normalized_name

    @staticmethod
    def _validate_ticket(ticket: str) -> str:
        if not isinstance(ticket, str):
            raise QueueError("Ticket must be a string.")
        normalized_ticket = ticket.strip()
        if not normalized_ticket:
            raise QueueError("Ticket cannot be empty.")
        return normalized_ticket

    @staticmethod
    def _validate_record_id(record_id: int) -> int:
        if isinstance(record_id, bool) or not isinstance(record_id, int):
            raise QueueError("Record ID must be an integer.")
        if record_id <= 0:
            raise QueueError("Record ID must be greater than zero.")
        return record_id

    def join_queue(self, customer_name: str) -> str:
        """Add a customer to the queue and return their ticket.

        Args:
            customer_name: Customer name to enqueue.

        Returns:
            Generated ticket value.

        Raises:
            QueueError: If the input is invalid or duplicate names are blocked.
        """
        validated_name = self._validate_name(customer_name)

        if (
            not self._allow_duplicate_waiting_names
            and self._repository.exists_waiting_name(validated_name, WAITING_STATUS)
        ):
            raise QueueError(f"{validated_name} is already waiting in the queue.")

        return self._repository.enqueue_customer(
            validated_name,
            WAITING_STATUS,
            TICKET_PREFIX,
            TICKET_NUMBER_WIDTH,
        )

    def call_next(self) -> ServingRow | None:
        """Move the next waiting customer to serving.

        Returns:
            Tuple of (ticket, name) when a customer is called, or None when queue is empty.

        Raises:
            QueueFullError: If someone is already being served.
        """
        if self._repository.any_with_status(SERVING_STATUS):
            raise QueueFullError(ALREADY_SERVING_MESSAGE)

        next_customer = self._repository.get_first_by_status(WAITING_STATUS)
        if next_customer is None:
            return None

        customer_id, ticket, customer_name = next_customer
        self._repository.update_status(customer_id, SERVING_STATUS)
        return ticket, customer_name

    def mark_done(self) -> ServingRow | None:
        """Mark the current serving customer as done.

        Returns:
            Tuple of (ticket, name) when a customer is marked done, or None when absent.
        """
        serving_customer = self._repository.get_first_by_status(SERVING_STATUS)
        if serving_customer is None:
            return None

        customer_id, ticket, customer_name = serving_customer
        self._repository.update_status(customer_id, DONE_STATUS)
        return ticket, customer_name

    def get_waiting(self) -> list[WaitingRow]:
        """Return waiting customers ordered by arrival."""
        return self._repository.list_waiting(WAITING_STATUS)

    def get_serving(self) -> ServingRow | None:
        """Return the customer currently being served."""
        return self._repository.get_serving(SERVING_STATUS)

    def get_history(self) -> list[HistoryRow]:
        """Return all queue records ordered by arrival."""
        return self._repository.list_history()

    def get_all_records(self) -> list[RecordRow]:
        """Return all records including database ids."""
        return self._repository.list_all_records()

    def count_waiting(self) -> int:
        """Return number of customers in waiting state."""
        return self._repository.count_by_status(WAITING_STATUS)

    def get_stats(self) -> dict[str, int]:
        """Return per-status counters plus total count."""
        counts_by_status = {
            WAITING_STATUS: 0,
            SERVING_STATUS: 0,
            DONE_STATUS: 0,
        }
        total_records = 0

        for status_name, status_count in self._repository.status_counts():
            total_records += status_count
            if status_name in counts_by_status:
                counts_by_status[status_name] = status_count

        counts_by_status[TOTAL_KEY] = total_records
        return counts_by_status

    def get_waiting_position(self, ticket: str) -> int:
        """Return number of waiting customers ahead of a ticket."""
        validated_ticket = self._validate_ticket(ticket)
        customer_id = self._repository.customer_id_by_ticket(validated_ticket)
        if customer_id is None:
            return 0
        return self._repository.count_waiting_before(customer_id, WAITING_STATUS)

    def delete_record(self, record_id: int) -> ServingRow | None:
        """Delete a record by id and return its (ticket, name) when found."""
        validated_record_id = self._validate_record_id(record_id)
        record = self._repository.record_by_id(validated_record_id)
        if record is None:
            return None
        self._repository.delete_by_id(validated_record_id)
        return record

    def clear_all_records(self) -> int:
        """Delete all records and return the number removed."""
        total_records = self._repository.count_records()
        if total_records > 0:
            self._repository.clear_all_records()
        return total_records


_DEFAULT_QUEUE_SERVICE = QueueService(repository=get_repository())


def _service() -> QueueService:
    return _DEFAULT_QUEUE_SERVICE


def join_queue(name: str) -> str:
    """Add a customer to the queue and return their ticket."""
    return _service().join_queue(name)


def call_next() -> ServingRow | None:
    """Move the next waiting customer to serving and return (ticket, name)."""
    return _service().call_next()


def mark_done() -> ServingRow | None:
    """Mark the currently serving customer as done and return (ticket, name)."""
    return _service().mark_done()


def get_waiting() -> list[WaitingRow]:
    """Return waiting customers as (ticket, name, created_at)."""
    return _service().get_waiting()


def get_serving() -> ServingRow | None:
    """Return the currently serving customer as (ticket, name)."""
    return _service().get_serving()


def get_history() -> list[HistoryRow]:
    """Return full queue history."""
    return _service().get_history()


def get_all_records() -> list[RecordRow]:
    """Return all queue records including record ids."""
    return _service().get_all_records()


def count_waiting() -> int:
    """Return count of waiting customers."""
    return _service().count_waiting()


def get_stats() -> dict[str, int]:
    """Return per-status counts and total."""
    return _service().get_stats()


def get_waiting_position(ticket: str) -> int:
    """Return queue position of a ticket as people-ahead count."""
    return _service().get_waiting_position(ticket)


def delete_record(record_id: int) -> ServingRow | None:
    """Delete a record by id and return (ticket, name) when found."""
    return _service().delete_record(record_id)


def clear_all_records() -> int:
    """Delete all records and return deleted row count."""
    return _service().clear_all_records()
