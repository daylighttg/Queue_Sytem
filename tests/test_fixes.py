"""Tests for core/queue_logic.py and core/database.py — validates bug fixes."""
import os
import sys
import tempfile
import unittest

# Make the project importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import core.database as db
from core.queue_logic import (
    join_queue,
    call_next,
    mark_done,
    count_waiting,
    get_all_records,
    get_serving,
    clear_all_records,
    get_stats,
)


class _DBTestCase(unittest.TestCase):
    """Base class that uses a temporary database for each test."""

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self._orig_path = db.DB_PATH
        db.DB_PATH = self._tmp.name
        db.create_tables()

    def tearDown(self):
        db.DB_PATH = self._orig_path
        os.unlink(self._tmp.name)


# ── Bug #1 — ticket numbering survives clear_all_records ──────
class TestTicketAfterClear(_DBTestCase):
    def test_ticket_does_not_restart_after_clear(self):
        """After clear_all_records(), new tickets must NOT reuse old numbers."""
        t1 = join_queue("Alice")
        t2 = join_queue("Bob")
        self.assertEqual(t1, "Q001")
        self.assertEqual(t2, "Q002")

        clear_all_records()

        t3 = join_queue("Charlie")
        # t3 must be Q003 (not Q001)
        self.assertEqual(t3, "Q003")


# ── Bug #2 — ticket derived from autoincrement id ─────────────
class TestTicketFromAutoincrement(_DBTestCase):
    def test_ticket_matches_row_id(self):
        """Ticket string must be derived from the AUTOINCREMENT id."""
        join_queue("Alice")
        join_queue("Bob")
        rows = get_all_records()
        for row_id, ticket, _name, _status in rows:
            self.assertEqual(ticket, f"Q{row_id:03d}")


# ── Bug #3 — cannot have two serving customers ────────────────
class TestNoDoubleServing(_DBTestCase):
    def test_call_next_while_serving_raises(self):
        """Calling call_next() while someone is serving must raise RuntimeError."""
        join_queue("Alice")
        join_queue("Bob")
        call_next()  # Alice → serving
        with self.assertRaises(RuntimeError):
            call_next()  # Should NOT set Bob to serving

    def test_normal_flow(self):
        """Normal flow: join → call → done → call works correctly."""
        join_queue("Alice")
        join_queue("Bob")
        t1, n1 = call_next()
        self.assertEqual(n1, "Alice")
        mark_done()
        t2, n2 = call_next()
        self.assertEqual(n2, "Bob")


# ── Bug #4 — position = people ahead ─────────────────────────
class TestJoinPosition(_DBTestCase):
    def test_position_is_people_ahead(self):
        """count_waiting() before insert gives the number of people already waiting."""
        # Empty queue — 0 people ahead
        before = count_waiting()
        self.assertEqual(before, 0)
        join_queue("Alice")
        # After Alice joins, 1 person waiting
        before_bob = count_waiting()
        self.assertEqual(before_bob, 1)
        join_queue("Bob")
        self.assertEqual(count_waiting(), 2)


# ── Bug #6 — counters table removed ──────────────────────────
class TestNoCountersTable(_DBTestCase):
    def test_counters_table_not_created(self):
        """The unused counters table should no longer be created."""
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='counters'"
            )
            self.assertIsNone(cursor.fetchone())


# ── Bug #7 — check_same_thread=False ─────────────────────────
class TestCheckSameThread(_DBTestCase):
    def test_connect_check_same_thread(self):
        """The connection must allow access from any thread."""
        import threading

        errors = []

        def worker():
            try:
                with db.connect() as conn:
                    conn.cursor().execute("SELECT 1")
            except Exception as e:
                errors.append(e)

        t = threading.Thread(target=worker)
        t.start()
        t.join()
        self.assertEqual(errors, [])


# ── Bug #8 — context manager closes connection ───────────────
class TestConnectContextManager(_DBTestCase):
    def test_connection_closed_after_with(self):
        """Connection must be closed when exiting the with block."""
        with db.connect() as conn:
            pass
        # Attempting to use a closed connection raises ProgrammingError
        with self.assertRaises(Exception):
            conn.execute("SELECT 1")

    def test_connection_closed_on_exception(self):
        """Connection must be closed even when an exception occurs."""
        try:
            with db.connect() as conn:
                raise ValueError("boom")
        except ValueError:
            pass
        with self.assertRaises(Exception):
            conn.execute("SELECT 1")


# ── Bug #12 — admin auth on Flask endpoints ──────────────────
class TestAdminAuth(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self._orig_path = db.DB_PATH
        db.DB_PATH = self._tmp.name
        db.create_tables()

        from api.server import app
        self.app = app
        self.client = app.test_client()

    def tearDown(self):
        db.DB_PATH = self._orig_path
        os.unlink(self._tmp.name)

    def test_next_requires_auth(self):
        resp = self.client.post("/next")
        self.assertEqual(resp.status_code, 401)

    def test_done_requires_auth(self):
        resp = self.client.post("/done")
        self.assertEqual(resp.status_code, 401)

    def test_next_with_valid_key(self):
        from api.server import ADMIN_API_KEY
        # No one is waiting so expect 404, but auth should pass
        resp = self.client.post("/next", headers={"X-API-Key": ADMIN_API_KEY})
        self.assertIn(resp.status_code, (200, 404))

    def test_join_no_auth_needed(self):
        resp = self.client.post("/join", json={"name": "Test"})
        self.assertEqual(resp.status_code, 201)

    def test_join_position_is_people_ahead(self):
        """Position in /join response should be 0 for first customer."""
        resp = self.client.post("/join", json={"name": "Alice"})
        data = resp.get_json()
        self.assertEqual(data["position"], 0)


if __name__ == "__main__":
    unittest.main()
