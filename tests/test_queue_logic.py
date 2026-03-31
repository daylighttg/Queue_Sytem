"""Pytest unit tests for queue logic using a mocked repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from core.queue_logic import QueueService
from core.exceptions import QueueError, QueueFullError


@dataclass
class _Record:
    """Simple in-memory representation of a customer row."""

    record_id: int
    ticket: str
    name: str
    status: str
    created_at: str


class MockQueueRepository:
    """In-memory repository that mimics the database contract for tests."""

    def __init__(self) -> None:
        self._records: list[_Record] = []
        self._next_id = 1

    def enqueue_customer(
        self,
        customer_name: str,
        waiting_status: str,
        ticket_prefix: str,
        ticket_width: int,
    ) -> str:
        record_id = self._next_id
        self._next_id += 1
        ticket = f"{ticket_prefix}{record_id:0{ticket_width}d}"
        self._records.append(
            _Record(
                record_id=record_id,
                ticket=ticket,
                name=customer_name,
                status=waiting_status,
                created_at="2026-01-01 00:00:00",
            )
        )
        return ticket

    def get_first_by_status(self, status: str) -> tuple[int, str, str] | None:
        for record in self._records:
            if record.status == status:
                return record.record_id, record.ticket, record.name
        return None

    def any_with_status(self, status: str) -> bool:
        return any(record.status == status for record in self._records)

    def update_status(self, customer_id: int, status: str) -> None:
        for record in self._records:
            if record.record_id == customer_id:
                record.status = status
                return

    def list_waiting(self, waiting_status: str) -> list[tuple[str, str, str]]:
        return [
            (record.ticket, record.name, record.created_at)
            for record in self._records
            if record.status == waiting_status
        ]

    def get_serving(self, serving_status: str) -> tuple[str, str] | None:
        for record in self._records:
            if record.status == serving_status:
                return record.ticket, record.name
        return None

    def list_history(self) -> list[tuple[str, str, str, str]]:
        return [
            (record.ticket, record.name, record.status, record.created_at)
            for record in self._records
        ]

    def list_all_records(self) -> list[tuple[int, str, str, str]]:
        return [
            (record.record_id, record.ticket, record.name, record.status)
            for record in self._records
        ]

    def count_by_status(self, status: str) -> int:
        return sum(1 for record in self._records if record.status == status)

    def status_counts(self) -> list[tuple[str, int]]:
        status_totals: dict[str, int] = {}
        for record in self._records:
            status_totals[record.status] = status_totals.get(record.status, 0) + 1
        return list(status_totals.items())

    def customer_id_by_ticket(self, ticket: str) -> int | None:
        for record in self._records:
            if record.ticket == ticket:
                return record.record_id
        return None

    def count_waiting_before(self, customer_id: int, waiting_status: str) -> int:
        return sum(
            1
            for record in self._records
            if record.status == waiting_status and record.record_id < customer_id
        )

    def record_by_id(self, record_id: int) -> tuple[str, str] | None:
        for record in self._records:
            if record.record_id == record_id:
                return record.ticket, record.name
        return None

    def delete_by_id(self, record_id: int) -> None:
        self._records = [record for record in self._records if record.record_id != record_id]

    def count_records(self) -> int:
        return len(self._records)

    def clear_all_records(self) -> None:
        self._records = []

    def exists_waiting_name(self, customer_name: str, waiting_status: str) -> bool:
        return any(
            record.name == customer_name and record.status == waiting_status
            for record in self._records
        )


@pytest.fixture
def queue_service() -> QueueService:
    """Provide a QueueService instance backed by a mocked repository."""
    return QueueService(repository=MockQueueRepository())


def test_enqueue_adds_customer_and_returns_ticket(queue_service: QueueService) -> None:
    """enqueue should create a ticket and increment waiting count."""
    generated_ticket = queue_service.join_queue("Alice")
    assert generated_ticket == "Q001"
    assert queue_service.count_waiting() == 1


def test_dequeue_returns_first_waiting_customer(queue_service: QueueService) -> None:
    """dequeue should serve customers in FIFO order."""
    queue_service.join_queue("Alice")
    queue_service.join_queue("Bob")

    first_called = queue_service.call_next()
    assert first_called == ("Q001", "Alice")


def test_peek_returns_current_serving_customer(queue_service: QueueService) -> None:
    """peek should report the customer currently being served."""
    queue_service.join_queue("Alice")
    queue_service.call_next()

    serving_customer = queue_service.get_serving()
    assert serving_customer == ("Q001", "Alice")


def test_empty_queue_behavior_returns_none(queue_service: QueueService) -> None:
    """Operations on an empty queue should return None where applicable."""
    assert queue_service.call_next() is None
    assert queue_service.mark_done() is None


def test_full_queue_behavior_raises_queue_full_error(queue_service: QueueService) -> None:
    """Calling next while someone is already serving should fail."""
    queue_service.join_queue("Alice")
    queue_service.join_queue("Bob")
    queue_service.call_next()

    with pytest.raises(QueueFullError):
        queue_service.call_next()


@pytest.mark.parametrize(
    "method_name, argument",
    [
        ("join_queue", None),
        ("join_queue", ""),
        ("get_waiting_position", None),
        ("delete_record", 0),
    ],
)
def test_invalid_input_raises_queue_error(
    queue_service: QueueService,
    method_name: str,
    argument: Any,
) -> None:
    """Public methods should validate input and reject invalid values."""
    with pytest.raises(QueueError):
        getattr(queue_service, method_name)(argument)

