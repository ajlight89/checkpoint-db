"""Entry point for ``python -m checkpoint``."""

from checkpoint import __version__


def main() -> None:
    """Run the Checkpoint-DB application."""
    print(f"Checkpoint-DB {__version__}")


if __name__ == "__main__":
    main()
