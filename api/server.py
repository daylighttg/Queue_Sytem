"""
api/server.py — Flask REST API for the Queue System.
Turns this PC into a mini server that the Android phone talks to.

Endpoints
─────────
POST /join      Customer joins the queue    → { "ticket": "Q005", "name": "…", "position": 3 }
GET  /queue     List everyone waiting       → { "waiting": […], "count": N }
GET  /status    Who is being served now     → { "serving": {…}, "waiting": N }
POST /next      Admin calls next customer   → { "ticket": "…", "name": "…" }  (requires X-API-Key)
POST /done      Admin marks customer done   → { "ticket": "…", "name": "…" }  (requires X-API-Key)
GET  /history   Full record history         → { "records": […], "count": N }
"""

import os
from functools import wraps

from flask import Flask, request, jsonify
from core.queue_logic import (
    join_queue,
    call_next,
    mark_done,
    get_waiting,
    get_serving,
    get_history,
    count_waiting,
)

app = Flask(__name__)

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "changeme")


def require_admin(f):
    """Decorator that checks for a valid X-API-Key header on admin endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-Key", "")
        if key != ADMIN_API_KEY:
            return jsonify({"error": "Unauthorized. Provide a valid X-API-Key header."}), 401
        return f(*args, **kwargs)
    return decorated


# ── POST /join ─────────────────────────────────────────────────
@app.route("/join", methods=["POST"])
def join():
    """Receives a customer name → saves to database → replies with ticket & position."""
    data = request.get_json(silent=True)
    if not data or not data.get("name", "").strip():
        return jsonify({"error": "Name is required."}), 400

    name = data["name"].strip()
    position = count_waiting()
    ticket = join_queue(name)
    return jsonify({"ticket": ticket, "name": name, "position": position}), 201


# ── GET /queue ─────────────────────────────────────────────────
@app.route("/queue", methods=["GET"])
def queue():
    """Returns the full waiting list."""
    rows = get_waiting()
    waiting = [
        {"ticket": ticket, "name": name, "position": i, "created_at": created_at}
        for i, (ticket, name, created_at) in enumerate(rows, start=1)
    ]
    return jsonify({"waiting": waiting, "count": len(waiting)}), 200


# ── GET /status ────────────────────────────────────────────────
@app.route("/status", methods=["GET"])
def status():
    """Returns who is currently being served and how many are waiting."""
    serving_row = get_serving()
    serving = (
        {"ticket": serving_row[0], "name": serving_row[1]} if serving_row else None
    )
    return jsonify({"serving": serving, "waiting": count_waiting()}), 200


# ── POST /next ─────────────────────────────────────────────────
@app.route("/next", methods=["POST"])
@require_admin
def next_customer():
    """Admin calls the next waiting customer → sets status to 'serving'."""
    try:
        result = call_next()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 409
    if result is None:
        return jsonify({"error": "No one is waiting in the queue."}), 404
    ticket, name = result
    return jsonify({"ticket": ticket, "name": name}), 200


# ── POST /done ─────────────────────────────────────────────────
@app.route("/done", methods=["POST"])
@require_admin
def done():
    """Admin marks the currently serving customer as done."""
    result = mark_done()
    if result is None:
        return jsonify({"error": "No customer is currently being served."}), 404
    ticket, name = result
    return jsonify({"ticket": ticket, "name": name}), 200


# ── GET /history ───────────────────────────────────────────────
@app.route("/history", methods=["GET"])
def history():
    """Returns every customer record (waiting, serving, done)."""
    rows = get_history()
    records = [
        {"ticket": ticket, "name": name, "status": status_val, "created_at": created_at}
        for ticket, name, status_val, created_at in rows
    ]
    return jsonify({"records": records, "count": len(records)}), 200


# ── Run the server ─────────────────────────────────────────────
if __name__ == "__main__":
    from core.database import create_tables

    create_tables()
    print("🚀 Queue System Flask Server starting …")
    print("   Other devices on the same Wi-Fi can reach this at")
    print("   http://<YOUR-PC-IP>:5000")
    print("   (find your IP with  ipconfig  in a terminal)\n")
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG", "0") == "1")
