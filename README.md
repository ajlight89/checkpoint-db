# Checkpoint-DB

An operations database for Checkpoint Games, a fictional store that buys, trades, and sells new and used video games, consoles, and accessories. Built with SQLite and Python for CPTR320 Database Management Systems (Fall 2026).

The database records the product catalog, stock by condition, customers and loyalty members, sales, and trade-ins. A command-line application gives store staff a menu for each of three roles:

- **Clerk:** list stock, find games in stock for a platform, look up and add customers, enroll loyalty members, and record sales and trade-ins.
- **Manager:** see low stock and loyalty members, and run reports on purchases per member, used games priced above their condition's average, members who bought every type of product, and products with no recent sales.
- **Analyst:** see sale lines, game units sold by platform, and sale totals.

Each sale and trade-in is saved in one transaction, so it is stored with all of its lines and stock changes or not at all. Active loyalty members receive 10% off each sale line.

## Download

The [Releases page](https://github.com/ajlight89/checkpoint-db/releases) has a Windows program, `Checkpoint-DB.exe`, that runs without Python. Double-click it to start. On the first run it creates `checkpoint.db` in the same folder and fills it with sample data; later runs open that file.

Windows may warn that the program is unrecognized because it is not signed. Choose **More info**, then **Run anyway**.

## Requirements

To run from source: Python 3.12 or later. Checkpoint-DB uses only the standard library; pytest is needed only for the tests.

## Setup

On Windows, in PowerShell:

```powershell
git clone git@github.com:ajlight89/checkpoint-db.git
Set-Location checkpoint-db
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Running Checkpoint-DB

With the virtual environment active, from the project folder:

```powershell
checkpoint    # the menu (or: python -m checkpoint)
pytest        # automated tests
```

The first run creates `checkpoint.db` in the current folder with sample data. Delete the file to start over with fresh sample data.

## Building the Windows program

With PyInstaller installed (`python -m pip install pyinstaller`), run from the project folder:

```powershell
pyinstaller --onefile --name Checkpoint-DB --paths src --add-data "src\checkpoint\sql;checkpoint\sql" src\checkpoint\__main__.py
```

`--add-data` bundles the SQL scripts that the program runs when it builds a new database. `Checkpoint-DB.exe` is written to `dist/`.

## Documentation

The `docs` folder holds the database design:

- [01-requirements.md](docs/01-requirements.md): the store's requirements and business rules.
- [02-eer-model.md](docs/02-eer-model.md): the EER model and diagram.
- [03-relational-schema.md](docs/03-relational-schema.md): the relational schema, normalization to BCNF, where each rule is enforced, and how a sale is recorded.
- [04-queries.md](docs/04-queries.md): the six report queries in SQL, relational algebra, and, for some, tuple relational calculus.

## Project layout

- `src/checkpoint/sql/` holds the SQL scripts: the schema, triggers, views, and sample data.
- `src/checkpoint/db.py` opens connections, runs transactions, and builds a database from the scripts.
- `src/checkpoint/queries.py` holds the report queries.
- `src/checkpoint/services.py` holds the store workflows: customers, loyalty enrollment, sales, and trade-ins. It never prints or asks for input.
- `src/checkpoint/money.py` keeps amounts in whole cents and works out the member discount.
- `src/checkpoint/cli.py` is the menu for each role.
- `tests/` holds the automated tests.
