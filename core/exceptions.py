"""Custom exception hierarchy for the Queue System."""


class QueueError(RuntimeError):
    """Base exception for all queue-system related failures."""


class QueueFullError(QueueError):
    """Raised when an operation cannot continue because the queue is already at maximum capacity."""


class QueueEmptyError(QueueError):
    """Raised when an operation requires queue data but none is available."""


class DatabaseError(QueueError):
    """Raised when a database operation fails."""

