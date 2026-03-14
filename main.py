from core.database import create_tables
from core.queue_logic import (
    join_queue,
    call_next,
    mark_done,
    get_waiting,
    get_history,
    get_all_records,
    delete_record,
    clear_all_records,
)


def show_menu():
    """Prints the main menu options."""
    print("\n=============================")
    print("   🏥  QUEUE SYSTEM MENU")
    print("=============================")
    print("  [1]  Join Queue")
    print("  [2]  Call Next Customer")
    print("  [3]  Mark Customer as Done")
    print("  [4]  View Waiting Queue")
    print("  [5]  View Full History")
    print("  [6]  Delete a Record")
    print("  [7]  Clear All Records")
    print("  [0]  Exit")
    print("=============================")


def handle_join_queue():
    name = input("Enter customer name: ").strip()
    if name:
        ticket = join_queue(name)
        print(f"\n🎫 Welcome {name}! Your ticket is {ticket}")
    else:
        print("\n⚠️  Name cannot be empty.")


def handle_call_next():
    try:
        result = call_next()
    except RuntimeError as e:
        print(f"\n⚠️  {e}")
        return
    if result is None:
        print("\n📭 No one is waiting in the queue.")
    else:
        ticket, name = result
        print(f"\n📢 Now serving: {name} — Ticket {ticket}")


def handle_mark_done():
    result = mark_done()
    if result is None:
        print("\n⚠️  No customer is currently being served.")
    else:
        ticket, name = result
        print(f"\n✅ {name} (Ticket {ticket}) has been marked as done.")


def handle_view_queue():
    rows = get_waiting()
    if not rows:
        print("\n📭 The queue is empty — no one is waiting.")
        return
    print("\n--- 🕐 Waiting Queue ---")
    for ticket, name, created_at in rows:
        print(f"  {ticket}  |  {name}  |  Joined: {created_at}")
    print(f"  Total waiting: {len(rows)}")


def handle_view_history():
    rows = get_history()
    if not rows:
        print("\n📭 No records found.")
        return
    print("\n--- 📋 Full History ---")
    for ticket, name, status, created_at in rows:
        print(f"  {ticket}  |  {name}  |  {status.upper()}  |  {created_at}")
    print(f"  Total records: {len(rows)}")


def handle_delete_record():
    rows = get_all_records()
    if not rows:
        print("\n📭 No records found.")
        return
    print("\n--- 🗑️  Delete Record ---")
    for record_id, ticket, name, status in rows:
        print(f"  ID: {record_id}  |  {ticket}  |  {name}  |  {status.upper()}")
    try:
        record_id = int(
            input("\nEnter the ID to delete (or 0 to cancel): ").strip()
        )
        if record_id == 0:
            print("❌ Deletion cancelled.")
            return
        record_info = next(
            ((t, n) for rid, t, n, s in rows if rid == record_id), None
        )
        if record_info is None:
            print(f"\n❌ Record with ID {record_id} not found.")
            return
        ticket, name = record_info
        confirm = input(
            f"\n⚠️  Delete {ticket} ({name})? (yes/no): "
        ).strip().lower()
        if confirm == "yes":
            delete_record(record_id)
            print(f"\n✅ Record {ticket} ({name}) has been deleted.")
        else:
            print("❌ Deletion cancelled.")
    except ValueError:
        print("\n❌ Invalid input. Please enter a valid ID number.")


def handle_clear_all_records():
    rows = get_all_records()
    count = len(rows)
    if count == 0:
        print("\n📭 No records to clear.")
        return
    print(f"\n⚠️  WARNING: You are about to delete ALL {count} records!")
    confirm = input("Type 'DELETE ALL' to confirm or press Enter to cancel: ").strip()
    if confirm == "DELETE ALL":
        clear_all_records()
        print(f"\n✅ All {count} records have been deleted.")
    else:
        print("❌ Clear operation cancelled.")


def main():
    """Main loop — initialises the database then keeps showing the menu."""
    create_tables()

    handlers = {
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
        choice = input("Enter your choice: ").strip()

        if choice == "0":
            print("\n👋 Goodbye! Queue system closed.")
            break
        elif choice in handlers:
            handlers[choice]()
        else:
            print("\n❌ Invalid choice. Please pick a number from the menu.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Queue system closed.")
