from core.database import connect


# ── Ticket helper ──────────────────────────────────────────────
def generate_ticket():
    """Returns the next ticket string (Q001, Q002, …) based on the last id."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM customers ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    next_number = (row[0] + 1) if row else 1
    return f"Q{next_number:03d}"


# ── 1. Join Queue ──────────────────────────────────────────────
def join_queue(name):
    """Adds a new customer with 'waiting' status. Returns the generated ticket string."""
    ticket = generate_ticket()
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO customers (ticket, name, status) VALUES (?, ?, 'waiting')",
        (ticket, name),
    )
    conn.commit()
    conn.close()
    return ticket


# ── 2. Call Next ───────────────────────────────────────────────
def call_next():
    """Sets the first waiting customer to 'serving'. Returns (ticket, name) or None."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, ticket, name FROM customers WHERE status = 'waiting' ORDER BY id ASC LIMIT 1"
    )
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return None
    customer_id, ticket, name = row
    cursor.execute(
        "UPDATE customers SET status = 'serving' WHERE id = ?", (customer_id,)
    )
    conn.commit()
    conn.close()
    return ticket, name


# ── 3. Mark Done ───────────────────────────────────────────────
def mark_done():
    """Marks the serving customer as 'done'. Returns (ticket, name) or None."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, ticket, name FROM customers WHERE status = 'serving' ORDER BY id ASC LIMIT 1"
    )
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return None
    customer_id, ticket, name = row
    cursor.execute(
        "UPDATE customers SET status = 'done' WHERE id = ?", (customer_id,)
    )
    conn.commit()
    conn.close()
    return ticket, name


# ── 4. Read helpers ────────────────────────────────────────────
def get_waiting():
    """Returns list of (ticket, name, created_at) for all waiting customers."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ticket, name, created_at FROM customers WHERE status = 'waiting' ORDER BY id ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_serving():
    """Returns (ticket, name) of the customer being served, or None."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ticket, name FROM customers WHERE status = 'serving' ORDER BY id ASC LIMIT 1"
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_history():
    """Returns list of (ticket, name, status, created_at) for every customer."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ticket, name, status, created_at FROM customers ORDER BY id ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_records():
    """Returns list of (id, ticket, name, status) for every customer."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, ticket, name, status FROM customers ORDER BY id ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def count_waiting():
    """Returns the number of customers with 'waiting' status."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'waiting'")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_stats():
    """Returns a dict with per-status counts and a total."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) FROM customers GROUP BY status")
    rows = cursor.fetchall()
    conn.close()
    stats = {"waiting": 0, "serving": 0, "done": 0, "total": 0}
    for status, count in rows:
        if status in stats:
            stats[status] = count
        stats["total"] += count
    return stats


# ── 5. Delete / Clear ──────────────────────────────────────────
def delete_record(record_id):
    """Deletes the customer with the given id. Returns (ticket, name) or None if not found."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT ticket, name FROM customers WHERE id = ?", (record_id,))
    record = cursor.fetchone()
    if record is None:
        conn.close()
        return None
    cursor.execute("DELETE FROM customers WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return record  # (ticket, name)


def clear_all_records():
    """Deletes all customer records. Returns the number of records deleted."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]
    if count > 0:
        cursor.execute("DELETE FROM customers")
        conn.commit()
    conn.close()
    return count
