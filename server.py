"""
server.py — Flask REST API for the Queue System.
Turns this PC into a mini server that the Android phone talks to.

Endpoints
─────────
POST /join      Customer joins the queue    → { "ticket": "Q005", "position": 3 }
GET  /queue     List everyone waiting       → [ { "ticket", "name", "position", "created_at" }, … ]
GET  /status    Who is being served now     → { "serving": { "ticket", "name" }, "waiting": 5 }
POST /next      Admin calls next customer   → { "ticket", "name" }
POST /done      Admin marks customer done   → { "ticket", "name" }
GET  /history   Full record history         → [ { "ticket", "name", "status", "created_at" }, … ]
"""

from flask import Flask, request, jsonify
from database import create_tables, connect
from queue_logic import generate_ticket

app = Flask(__name__)

# ── Initialise database on startup ────────────────────────────
create_tables()


# ── POST /join ────────────────────────────────────────────────
@app.route("/join", methods=["POST"])
def join():
    """Receives a customer name → saves to database → replies with ticket & position."""
    data = request.get_json(silent=True)

    if not data or not data.get("name", "").strip():
        return jsonify({"error": "Name is required."}), 400

    name = data["name"].strip()
    ticket = generate_ticket()

    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO customers (ticket, name, status) VALUES (?, ?, 'waiting')",
        (ticket, name),
    )
    conn.commit()

    # Calculate this customer's position (how many are waiting including them)
    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'waiting'")
    position = cursor.fetchone()[0]

    conn.close()
    return jsonify({"ticket": ticket, "name": name, "position": position}), 201


# ── GET /queue ────────────────────────────────────────────────
@app.route("/queue", methods=["GET"])
def queue():
    """Returns the full waiting list."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ticket, name, created_at FROM customers "
        "WHERE status = 'waiting' ORDER BY id ASC"
    )
    rows = cursor.fetchall()
    conn.close()

    waiting = []
    for i, (ticket, name, created_at) in enumerate(rows, start=1):
        waiting.append({
            "ticket": ticket,
            "name": name,
            "position": i,
            "created_at": created_at,
        })

    return jsonify({"waiting": waiting, "count": len(waiting)}), 200


# ── GET /status ───────────────────────────────────────────────
@app.route("/status", methods=["GET"])
def status():
    """Returns who is currently being served and how many are waiting."""
    conn = connect()
    cursor = conn.cursor()

    # Who is being served?
    cursor.execute(
        "SELECT ticket, name FROM customers WHERE status = 'serving' ORDER BY id ASC LIMIT 1"
    )
    serving_row = cursor.fetchone()

    # How many still waiting?
    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'waiting'")
    waiting_count = cursor.fetchone()[0]

    conn.close()

    serving = None
    if serving_row:
        serving = {"ticket": serving_row[0], "name": serving_row[1]}

    return jsonify({"serving": serving, "waiting": waiting_count}), 200


# ── POST /next ────────────────────────────────────────────────
@app.route("/next", methods=["POST"])
def next_customer():
    """Admin calls the next waiting customer → sets status to 'serving'."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, ticket, name FROM customers "
        "WHERE status = 'waiting' ORDER BY id ASC LIMIT 1"
    )
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return jsonify({"error": "No one is waiting in the queue."}), 404

    customer_id, ticket, name = row
    cursor.execute(
        "UPDATE customers SET status = 'serving' WHERE id = ?", (customer_id,)
    )
    conn.commit()
    conn.close()

    return jsonify({"ticket": ticket, "name": name}), 200


# ── POST /done ────────────────────────────────────────────────
@app.route("/done", methods=["POST"])
def done():
    """Admin marks the currently serving customer as done."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, ticket, name FROM customers "
        "WHERE status = 'serving' ORDER BY id ASC LIMIT 1"
    )
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return jsonify({"error": "No customer is currently being served."}), 404

    customer_id, ticket, name = row
    cursor.execute(
        "UPDATE customers SET status = 'done' WHERE id = ?", (customer_id,)
    )
    conn.commit()
    conn.close()

    return jsonify({"ticket": ticket, "name": name}), 200


# ── GET /history ──────────────────────────────────────────────
@app.route("/history", methods=["GET"])
def history():
    """Returns every customer record (waiting, serving, done)."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ticket, name, status, created_at FROM customers ORDER BY id ASC"
    )
    rows = cursor.fetchall()
    conn.close()

    records = []
    for ticket, name, status_val, created_at in rows:
        records.append({
            "ticket": ticket,
            "name": name,
            "status": status_val,
            "created_at": created_at,
        })

    return jsonify({"records": records, "count": len(records)}), 200


# ── Run the server ────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Queue System Flask Server starting …")
    print("   Other devices on the same Wi-Fi can reach this at")
    print("   http://<YOUR-PC-IP>:5000")
    print("   (find your IP with  ipconfig  in a terminal)\n")
    app.run(host="0.0.0.0", port=5000, debug=True)

