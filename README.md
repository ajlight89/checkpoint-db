# Checkpoint-DB

An operations database for Checkpoint Games, a fictional store that buys, trades, and sells new and used video games, consoles, and accessories. Built with SQLite and Python for CPTR320 Database Management Systems (Fall 2026).

The database will record the product catalog, stock by condition, customers and loyalty members, sales, and trade-ins, with a command-line application for store staff.

## Status

Early development: the package, database connection, and test setup are in place.

## Setup

Requires Python 3.12 or later. On Windows, in PowerShell:

```powershell
git clone git@github.com:ajlight89/checkpoint-db.git
Set-Location checkpoint-db
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
```
