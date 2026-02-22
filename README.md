# Queue System

A Python-based queue management system designed to handle queue operations with database persistence.

## Overview

This project implements a queue system that manages queue operations and stores queue data in a database. It provides core functionality for queue management, including queue creation, item addition, and retrieval.

## Project Structure

```
Queue_Sytem/
├── main.py              # Main entry point and application logic
├── queue_logic.py       # Core queue operations and business logic
├── database.py          # Database operations and persistence layer
└── .gitignore          # Git ignore configuration
```

### File Descriptions

- **main.py**: The primary entry point of the application. Handles the main program flow and user interactions.
- **queue_logic.py**: Contains the core queue logic and operations (enqueue, dequeue, peek, etc.).
- **database.py**: Manages all database-related operations including storing and retrieving queue data.

## Features

- Queue management operations
- Database persistence for queue data
- Modular architecture separating queue logic from database operations

## Requirements

- Python 3.6 or higher
- Any additional dependencies (see requirements below)

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

3. Install dependencies (if any):
```bash
pip install -r requirements.txt
```

## Usage

To run the queue system:

```bash
python main.py
```

Follow the on-screen prompts to interact with the queue system.

## How It Works

1. **Queue Logic** (`queue_logic.py`): Implements the queue data structure and operations
2. **Database Layer** (`database.py`): Handles persistence and data storage
3. **Main Application** (`main.py`): Orchestrates the queue operations and provides the interface

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is open source. Please check the repository for license information.

## Author

[daylighttg](https://github.com/daylighttg)

---

*For more information or questions, please open an issue in the repository.*
