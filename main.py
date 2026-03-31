"""CLI entry point for the Queue System."""

from __future__ import annotations

import logging
from typing import Callable

from core.database import create_tables
from core.queue_logic import (
    call_next,
    clear_all_records,
    delete_record,
    get_all_records,
    get_history,
    get_waiting,
    join_queue,
    mark_done,
)
from core.exceptions import QueueError

LOGGER = logging.getLogger(__name__)
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

MENU_SEPARATOR = "============================="
EXIT_CHOICE = "0"
DELETE_CONFIRMATION = "yes"
DELETE_ALL_CONFIRMATION = "DELETE ALL"


def configure_logging() -> None:
    """Configure application logging once for CLI execution."""
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


def show_menu() -> None:
    """Print the main menu options."""
    print(f"\n{MENU_SEPARATOR}")
    print("   🏥  QUEUE SYSTEM MENU")
    print(MENU_SEPARATOR)
    print("  [1]  Join Queue")
    print("  [2]  Call Next Customer")
    print("  [3]  Mark Customer as Done")
    print("  [4]  View Waiting Queue")
    print("  [5]  View Full History")
    print("  [6]  Delete a Record")
    print("  [7]  Clear All Records")
    print("  [0]  Exit")
    print(MENU_SEPARATOR)


def _parse_record_id(raw_value: str) -> int | None:
    raw_input_value = raw_value.strip()
    if not raw_input_value:
        return None
    try:
        return int(raw_input_value)
    except ValueError:
        return None


def _find_record_label(
    records: list[tuple[int, str, str, str]],
    target_record_id: int,
) -> tuple[str, str] | None:
    for record_id, ticket, customer_name, _status in records:
        if record_id == target_record_id:
            return ticket, customer_name
    return None


def handle_join_queue() -> None:
    """Prompt for a customer name and add it to the queue."""
    customer_name = input("Enter customer name: ").strip()
    if not customer_name:
        print("\n⚠️  Name cannot be empty.")
        return

    ticket = join_queue(customer_name)
    print(f"\n🎫 Welcome {customer_name}! Your ticket is {ticket}")


def handle_call_next() -> None:
    """Call the next waiting customer."""
    next_customer = call_next()
    if next_customer is None:
        print("\n📭 No one is waiting in the queue.")
        return

    ticket, customer_name = next_customer
    print(f"\n📢 Now serving: {customer_name} — Ticket {ticket}")


def handle_mark_done() -> None:
    """Mark the currently serving customer as done."""
    serving_customer = mark_done()
    if serving_customer is None:
        print("\n⚠️  No customer is currently being served.")
        return

    ticket, customer_name = serving_customer
    print(f"\n✅ {customer_name} (Ticket {ticket}) has been marked as done.")


def handle_view_queue() -> None:
    """Display waiting customers."""
    waiting_rows = get_waiting()
    if not waiting_rows:
        print("\n📭 The queue is empty — no one is waiting.")
        return

    print("\n--- 🕐 Waiting Queue ---")
    for ticket, customer_name, created_at in waiting_rows:
        print(f"  {ticket}  |  {customer_name}  |  Joined: {created_at}")
    print(f"  Total waiting: {len(waiting_rows)}")


def handle_view_history() -> None:
    """Display all queue history records."""
    history_rows = get_history()
    if not history_rows:
        print("\n📭 No records found.")
        return

    print("\n--- 📋 Full History ---")
    for ticket, customer_name, status, created_at in history_rows:
        print(f"  {ticket}  |  {customer_name}  |  {status.upper()}  |  {created_at}")
    print(f"  Total records: {len(history_rows)}")


def handle_delete_record() -> None:
    """Delete a selected record by id after confirmation."""
    all_records = get_all_records()
    if not all_records:
        print("\n📭 No records found.")
        return

    print("\n--- 🗑️  Delete Record ---")
    for record_id, ticket, customer_name, status in all_records:
        print(f"  ID: {record_id}  |  {ticket}  |  {customer_name}  |  {status.upper()}")

    parsed_record_id = _parse_record_id(
        input("\nEnter the ID to delete (or 0 to cancel): ")
    )
    if parsed_record_id is None:
        print("\n❌ Invalid input. Please enter a valid ID number.")
        return
    if parsed_record_id == 0:
        print("❌ Deletion cancelled.")
        return

    selected_record = _find_record_label(all_records, parsed_record_id)
    if selected_record is None:
        print(f"\n❌ Record with ID {parsed_record_id} not found.")
        return

    ticket, customer_name = selected_record
    confirmation = input(
        f"\n⚠️  Delete {ticket} ({customer_name})? (yes/no): "
    ).strip().lower()
    if confirmation != DELETE_CONFIRMATION:
        print("❌ Deletion cancelled.")
        return

    delete_record(parsed_record_id)
    print(f"\n✅ Record {ticket} ({customer_name}) has been deleted.")


def handle_clear_all_records() -> None:
    """Delete all records after explicit user confirmation."""
    all_records = get_all_records()
    total_records = len(all_records)
    if total_records == 0:
        print("\n📭 No records to clear.")
        return

    print(f"\n⚠️  WARNING: You are about to delete ALL {total_records} records!")
    confirmation = input(
        "Type 'DELETE ALL' to confirm or press Enter to cancel: "
    ).strip()
    if confirmation != DELETE_ALL_CONFIRMATION:
        print("❌ Clear operation cancelled.")
        return

    clear_all_records()
    print(f"\n✅ All {total_records} records have been deleted.")


def main() -> None:
    """Run the interactive queue CLI."""
    create_tables()

    handlers: dict[str, Callable[[], None]] = {
        "1": handle_join_queue,
        "2": handle_call_next,
        "3": handle_mark_done,
        "4": handle_view_queue,
        "5": handle_view_history,
        "6": handle_delete_record,
        "7": handle_clear_all_records,
    }

    while True:
        show_menu()
        selected_choice = input("Enter your choice: ").strip()

        if selected_choice == EXIT_CHOICE:
            print("\n👋 Goodbye! Queue system closed.")
            return

        selected_handler = handlers.get(selected_choice)
        if selected_handler is None:
            print("\n❌ Invalid choice. Please pick a number from the menu.")
            continue

        try:
            selected_handler()
        except QueueError as queue_error:
            LOGGER.error("Queue operation failed: %s", queue_error)
            print(f"\n⚠️  {queue_error}")
        except Exception as unexpected_error:  # pragma: no cover - defensive fallback
            LOGGER.exception("Unexpected application error: %s", unexpected_error)
            print("\n❌ An unexpected error occurred. Please try again.")


if __name__ == "__main__":
    configure_logging()
    try:
        main()
    except KeyboardInterrupt:
        LOGGER.info("CLI interrupted by user.")
        print("\n\n👋 Interrupted. Queue system closed.")
    except QueueError as fatal_queue_error:
        LOGGER.exception("Fatal queue error: %s", fatal_queue_error)
        print(f"\n❌ Fatal error: {fatal_queue_error}")
    except Exception as fatal_unexpected_error:  # pragma: no cover - defensive fallback
        LOGGER.exception("Fatal unexpected error: %s", fatal_unexpected_error)
        print("\n❌ Fatal unexpected error. Queue system closed.")
