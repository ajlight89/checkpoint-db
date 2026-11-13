"""Entry point for ``python -m checkpoint`` and the ``checkpoint`` command."""

from pathlib import Path

from checkpoint import __version__, cli, db

# The store's database file, created in the current folder on the first run.
DB_PATH = Path("checkpoint.db")


def main() -> None:
    """Open the store database, building it with sample rows on the first run."""
    print(f"Checkpoint-DB {__version__}")
    first_run = not DB_PATH.exists()
    conn = db.connect(DB_PATH)
    try:
        if first_run:
            db.initialize(conn)
            db.load_demo(conn)
            print(f"Created {DB_PATH} with sample data.")
        cli.main(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
