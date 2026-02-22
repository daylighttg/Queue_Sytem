from database import connect


# ── Ticket Helper ─────────────────────────────────────────────
def generate_ticket():
    """Returns the next ticket string (Q001, Q002, …) based on the last id."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM customers ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    next_number = (row[0] + 1) if row else 1
    return f"Q{next_number:03d}"


# ── 1. Join Queue ─────────────────────────────────────────────
def join_queue(name):
    """Adds a new customer with a generated ticket and 'waiting' status."""
    ticket = generate_ticket()
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO customers (ticket, name, status) VALUES (?, ?, 'waiting')",
        (ticket, name),
    )
    conn.commit()
    conn.close()
    print(f"\n🎫 Welcome {name}! Your ticket is {ticket}")


# ── 2. Call Next ──────────────────────────────────────────────
def call_next():
    """Finds the first waiting customer and sets their status to 'serving'."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, ticket, name FROM customers WHERE status = 'waiting' ORDER BY id ASC LIMIT 1"
    )
    row = cursor.fetchone()

    if row is None:
        print("\n📭 No one is waiting in the queue.")
        conn.close()
        return

    customer_id, ticket, name = row
    cursor.execute(
        "UPDATE customers SET status = 'serving' WHERE id = ?", (customer_id,)
    )
    conn.commit()
    conn.close()
    print(f"\n📢 Now serving: {name} — Ticket {ticket}")


# ── 3. Mark Done ──────────────────────────────────────────────
def mark_done():
    """Marks the currently serving customer as 'done'."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, ticket, name FROM customers WHERE status = 'serving' ORDER BY id ASC LIMIT 1"
    )
    row = cursor.fetchone()

    if row is None:
        print("\n⚠️  No customer is currently being served.")
        conn.close()
        return

    customer_id, ticket, name = row
    cursor.execute(
        "UPDATE customers SET status = 'done' WHERE id = ?", (customer_id,)
    )
    conn.commit()
    conn.close()
    print(f"\n✅ {name} (Ticket {ticket}) has been marked as done.")


# ── 4. View Queue ─────────────────────────────────────────────
def view_queue():
    """Prints all customers currently waiting."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ticket, name, created_at FROM customers WHERE status = 'waiting' ORDER BY id ASC"
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("\n📭 The queue is empty — no one is waiting.")
        return

    print("\n--- 🕐 Waiting Queue ---")
    for ticket, name, created_at in rows:
        print(f"  {ticket}  |  {name}  |  Joined: {created_at}")
    print(f"  Total waiting: {len(rows)}")


# ── 5. View History ───────────────────────────────────────────
def view_history():
    """Prints every customer record (waiting, serving, and done)."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ticket, name, status, created_at FROM customers ORDER BY id ASC"
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("\n📭 No records found.")
        return

    print("\n--- 📋 Full History ---")
    for ticket, name, status, created_at in rows:
        print(f"  {ticket}  |  {name}  |  {status.upper()}  |  {created_at}")
    print(f"  Total records: {len(rows)}")


# ── 6. Count Waiting ──────────────────────────────────────────
def count_waiting():
    """Returns (and prints) the number of customers still waiting."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'waiting'")
    count = cursor.fetchone()[0]
    conn.close()
    return count


# ── 7. Delete Record ──────────────────────────────────────────
def delete_record():
    """Allows user to delete a customer record by ticket number."""
    conn = connect()
    cursor = conn.cursor()

    # Show all records with IDs
    cursor.execute(
        "SELECT id, ticket, name, status FROM customers ORDER BY id ASC"
    )
    rows = cursor.fetchall()

    if not rows:
        print("\n📭 No records found.")
        conn.close()
        return

    print("\n--- 🗑️  Delete Record ---")
    for id, ticket, name, status in rows:
        print(f"  ID: {id}  |  {name}  |  {status.upper()}")

    try:
        record_id = int(input("\nEnter the ID number of the record to delete (or 0 to cancel): ").strip())

        if record_id == 0:
            print("❌ Deletion cancelled.")
            conn.close()
            return

        # Check if record exists
        cursor.execute("SELECT ticket, name FROM customers WHERE id = ?", (record_id,))
        record = cursor.fetchone()

        if record is None:
            print(f"\n❌ Record with ID {record_id} not found.")
            conn.close()
            return

        ticket, name = record
        # Confirm deletion
        confirm = input(f"\n⚠️  Are you sure you want to delete {ticket} ({name})? (yes/no): ").strip().lower()

        if confirm == "yes":
            cursor.execute("DELETE FROM customers WHERE id = ?", (record_id,))
            conn.commit()
            print(f"\n✅ Record {ticket} ({name}) has been deleted.")
        else:
            print("❌ Deletion cancelled.")

    except ValueError:
        print("\n❌ Invalid input. Please enter a valid ID number.")

    conn.close()


# ── 8. Clear All Records ──────────────────────────────────────
def clear_all_records():
    """Deletes all customer records after confirmation."""
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]

    if count == 0:
        print("\n📭 No records to clear.")
        conn.close()
        return

    print(f"\n⚠️  WARNING: You are about to delete ALL {count} records!")
    confirm = input("Type 'DELETE ALL' to confirm or press Enter to cancel: ").strip()

    if confirm == "DELETE ALL":
        cursor.execute("DELETE FROM customers")
        conn.commit()
        print(f"\n✅ All {count} records have been deleted.")
    else:
        print("❌ Clear operation cancelled.")

    conn.close()
