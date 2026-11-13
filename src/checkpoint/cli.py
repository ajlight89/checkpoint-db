"""Command-line menus for the clerk, manager, and analyst roles.

Each menu option asks for input, calls a query or a store workflow, and
prints the result. The rules live in ``services`` and in the database, so a
refused request comes back here as a StoreError with a message to show.
"""

import sqlite3
from collections.abc import Callable

from checkpoint import queries, services
from checkpoint.money import format_cents
from checkpoint.services import StoreError

# ----- Input helpers -----


def ask(prompt: str) -> str:
    """Return the user's answer with surrounding spaces removed."""
    return input(f"{prompt}: ").strip()


def ask_int(prompt: str, optional: bool = False) -> int | None:
    """Ask until the answer is a whole number greater than zero.

    If ``optional`` is true, a blank answer returns None.
    """
    while True:
        answer = ask(prompt)
        if optional and not answer:
            return None
        if answer.isdecimal() and int(answer) > 0:
            return int(answer)
        print("Enter a whole number greater than zero.")


def ask_choice(prompt: str, choices: dict[str, str]) -> str:
    """Ask until the answer is a key in ``choices``, and return its value."""
    options = ", ".join(f"{key} {value}" for key, value in choices.items())
    while True:
        answer = ask(f"{prompt} ({options})")
        if answer in choices:
            return choices[answer]
        print("Choose one of the listed options.")


# ----- Output helpers -----


def cell(value: object, is_money: bool) -> str:
    """Return a value as table text: blank for NULL, dollars for cents."""
    if value is None:
        return ""
    return format_cents(value) if is_money else str(value)


def show(
    headers: tuple[str, ...], rows: list[tuple], money: tuple[int, ...] = ()
) -> None:
    """Print rows as a table. ``money`` lists the column numbers that hold cents."""
    if not rows:
        print("No rows found.")
        return
    text = [[cell(v, i in money) for i, v in enumerate(row)] for row in rows]
    widths = [max(len(h), *(len(r[i]) for r in text)) for i, h in enumerate(headers)]

    def line(values: list[str]) -> str:
        cells = (
            v.rjust(w) if i in money else v.ljust(w)
            for i, (v, w) in enumerate(zip(values, widths, strict=True))
        )
        return "  ".join(cells).rstrip()

    print(line(list(headers)))
    print(line(["-" * w for w in widths]))
    for row in text:
        print(line(row))


# ----- Clerk -----


def stock(conn: sqlite3.Connection) -> None:
    """List every stock record with its prices (clerk_stock view)."""
    rows = conn.execute(
        "SELECT product_id, name, platform_name, condition, qty_on_hand, "
        "sell_price_cents, trade_value_cents FROM clerk_stock "
        "ORDER BY product_id, condition"
    ).fetchall()
    headers = ("ID", "Name", "Platform", "Condition", "Qty", "Price", "Trade")
    show(headers, rows, money=(5, 6))


def games_on_platform(conn: sqlite3.Connection) -> None:
    """List the games in stock for one platform (Q1)."""
    sql = "SELECT platform_id, platform_name FROM platform ORDER BY platform_id"
    show(("ID", "Platform"), conn.execute(sql).fetchall())
    rows = queries.in_stock_games(conn, ask_int("Platform id"))
    show(("Name", "Condition", "Qty", "Price"), rows, money=(3,))


def lookup_customer(conn: sqlite3.Connection) -> None:
    """Find a customer by phone number."""
    row = services.find_customer(conn, ask("Phone (10 digits)"))
    if row is None:
        print("No customer has that phone number.")
    else:
        show(("ID", "First", "Last", "Phone", "Joined", "Expires"), [row])


# ----- Menus -----

Action = Callable[[sqlite3.Connection], None]

# Each role's menu maps the key to type to (label, function to call).
MENUS: dict[str, dict[str, tuple[str, Action]]] = {
    "clerk": {
        "1": ("Stock list", stock),
        "2": ("Games in stock for a platform", games_on_platform),
        "3": ("Look up a customer", lookup_customer),
    },
}


def run_menu(conn: sqlite3.Connection, role: str) -> None:
    """Show one role's menu and run the chosen actions until the user goes back."""
    menu = MENUS[role]
    while True:
        print(f"\n{role.title()} menu")
        for key, (label, _) in menu.items():
            print(f"  {key}. {label}")
        print("  b. Back")
        choice = ask("Choice")
        if choice == "b":
            return
        if choice not in menu:
            print("Unknown choice.")
            continue
        _, action = menu[choice]
        try:
            action(conn)
        except StoreError as err:
            print(err)
        except KeyboardInterrupt:
            print("\nCancelled.")


def main(conn: sqlite3.Connection) -> None:
    """Ask for a role and run its menu until the user quits."""
    roles = {str(number): role for number, role in enumerate(MENUS, start=1)}
    roles["q"] = "quit"
    try:
        while True:
            role = ask_choice("\nRole", roles)
            if role == "quit":
                break
            run_menu(conn, role)
    except (KeyboardInterrupt, EOFError):
        print()
    print("Goodbye.")
