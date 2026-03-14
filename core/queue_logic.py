from core.database import connect


# ── 1. Join Queue ──────────────────────────────────────────────
def join_queue(name):
    """Adds a new customer with 'waiting' status. Returns the generated ticket string.

    The ticket is derived from the AUTOINCREMENT id so it remains unique even
    after ``clear_all_records()`` deletes all rows.  Everything happens inside
    a single connection to avoid race conditions.
    """
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (ticket, name, status) VALUES ('', ?, 'waiting')",
            (name,),
        )
        row_id = cursor.lastrowid
        ticket = f"Q{row_id:03d}"
        cursor.execute(
            "UPDATE customers SET ticket = ? WHERE id = ?", (ticket, row_id)
        )
        conn.commit()
        return ticket


# ── 2. Call Next ───────────────────────────────────────────────
def call_next():
    """Sets the first waiting customer to 'serving'. Returns (ticket, name) or None.

    Raises ``RuntimeError`` if a customer is already being served.
    """
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM customers WHERE status = 'serving' LIMIT 1"
        )
        if cursor.fetchone() is not None:
            raise RuntimeError("A customer is already being served. Mark them as done first.")
        cursor.execute(
            "SELECT id, ticket, name FROM customers WHERE status = 'waiting' ORDER BY id ASC LIMIT 1"
        )
        row = cursor.fetchone()
        if row is None:
            return None
        customer_id, ticket, name = row
        cursor.execute(
            "UPDATE customers SET status = 'serving' WHERE id = ?", (customer_id,)
        )
        conn.commit()
        return ticket, name


# ── 3. Mark Done ───────────────────────────────────────────────
def mark_done():
    """Marks the serving customer as 'done'. Returns (ticket, name) or None."""
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, ticket, name FROM customers WHERE status = 'serving' ORDER BY id ASC LIMIT 1"
        )
        row = cursor.fetchone()
        if row is None:
            return None
        customer_id, ticket, name = row
        cursor.execute(
            "UPDATE customers SET status = 'done' WHERE id = ?", (customer_id,)
        )
        conn.commit()
        return ticket, name


# ── 4. Read helpers ────────────────────────────────────────────
def get_waiting():
    """Returns list of (ticket, name, created_at) for all waiting customers."""
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ticket, name, created_at FROM customers WHERE status = 'waiting' ORDER BY id ASC"
        )
        return cursor.fetchall()


def get_serving():
    """Returns (ticket, name) of the customer being served, or None."""
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ticket, name FROM customers WHERE status = 'serving' ORDER BY id ASC LIMIT 1"
        )
        return cursor.fetchone()


def get_history():
    """Returns list of (ticket, name, status, created_at) for every customer."""
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ticket, name, status, created_at FROM customers ORDER BY id ASC"
        )
        return cursor.fetchall()


def get_all_records():
    """Returns list of (id, ticket, name, status) for every customer."""
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, ticket, name, status FROM customers ORDER BY id ASC"
        )
        return cursor.fetchall()


def count_waiting():
    """Returns the number of customers with 'waiting' status."""
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'waiting'")
        return cursor.fetchone()[0]


def get_stats():
    """Returns a dict with per-status counts and a total."""
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM customers GROUP BY status")
        rows = cursor.fetchall()
    stats = {"waiting": 0, "serving": 0, "done": 0, "total": 0}
    for status, count in rows:
        if status in stats:
            stats[status] = count
        stats["total"] += count
    return stats


# ── 5. Delete / Clear ──────────────────────────────────────────
def delete_record(record_id):
    """Deletes the customer with the given id. Returns (ticket, name) or None if not found."""
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ticket, name FROM customers WHERE id = ?", (record_id,))
        record = cursor.fetchone()
        if record is None:
            return None
        cursor.execute("DELETE FROM customers WHERE id = ?", (record_id,))
        conn.commit()
        return record  # (ticket, name)


def clear_all_records():
    """Deletes all customer records. Returns the number of records deleted."""
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers")
        count = cursor.fetchone()[0]
        if count > 0:
            cursor.execute("DELETE FROM customers")
            conn.commit()
        return count
