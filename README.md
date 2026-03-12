# Queue System

A Python-based queue management system with database persistence, a command-line interface, a desktop GUI, and a REST API.

## Project Structure

```
Queue_Sytem/
├── main.py              # CLI entry point
├── requirements.txt     # Python dependencies
├── core/                # Shared business logic & data layer
│   ├── __init__.py
│   ├── database.py      # SQLite connection and table setup
│   └── queue_logic.py   # All queue operations (join, call, done, …)
├── api/                 # Flask REST API
│   ├── __init__.py
│   └── server.py        # HTTP endpoints consumed by mobile / web clients
└── ui/                  # Tkinter desktop GUI
    ├── __init__.py
    └── ui_admin.py      # Admin GUI (join, call next, history, stats, …)
```

### Package descriptions

- **`core/database.py`** — Opens the SQLite connection and creates tables on first run. The database file (`queue_system.db`) is placed at the project root.
- **`core/queue_logic.py`** — Pure business-logic functions that return data (no printing). Used by the CLI, the API, and the GUI so there is no duplicated SQL.
- **`api/server.py`** — Flask REST server. Run it to expose the queue over HTTP on port 5000.
- **`ui/ui_admin.py`** — Tkinter admin GUI with live queue view, history, and statistics tabs.
- **`main.py`** — Interactive command-line interface.

## Features

- Join, call, and complete queue entries
- Full history and real-time statistics
- SQLite persistence — no extra database server required
- Three interfaces sharing the same core logic: CLI, GUI, REST API

## Requirements

- Python 3.6 or higher
- Flask (for the API server only)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/daylighttg/Queue_Sytem.git
cd Queue_Sytem
```

2. (Optional) Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command-line interface
```bash
python main.py
```

### Desktop GUI
```bash
python -m ui.ui_admin
```

### REST API server
```bash
python -m api.server
```
The server listens on `http://0.0.0.0:5000`. Other devices on the same network can reach it at `http://<YOUR-PC-IP>:5000`.

#### API endpoints

| Method | Path       | Description                          |
|--------|------------|--------------------------------------|
| POST   | `/join`    | Add a customer to the queue          |
| GET    | `/queue`   | List all waiting customers           |
| GET    | `/status`  | Who is being served / waiting count  |
| POST   | `/next`    | Call the next waiting customer       |
| POST   | `/done`    | Mark the serving customer as done    |
| GET    | `/history` | Full record history                  |

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is open source. Please check the repository for license information.

## Author

[daylighttg](https://github.com/daylighttg)

---

*For more information or questions, please open an issue in the repository.*

