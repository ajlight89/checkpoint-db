"""Command-line menus for the clerk, manager, and analyst roles.

Each menu option asks for input, calls a query or a store workflow, and
prints the result. The rules live in ``services`` and in the database, so a
refused request comes back here as a StoreError with a message to show.
"""

import sqlite3
from collections.abc import Callable
from datetime import date

from checkpoint import queries, services
from checkpoint.money import format_cents
from checkpoint.services import Line, StoreError

CONDITIONS = {"1": "new", "2": "used_complete", "3": "used_loose"}
PAYMENTS = {"1": "cash", "2": "card"}

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


def ask_date(prompt: str) -> str:
    """Ask until the answer is a date, and return it as 'YYYY-MM-DD'."""
    while True:
        try:
            return date.fromisoformat(ask(f"{prompt} (YYYY-MM-DD)")).isoformat()
        except ValueError:
            print("Enter a date such as 2026-11-01.")


def ask_choice(prompt: str, choices: dict[str, str]) -> str:
    """Ask until the answer is a key in ``choices``, and return its value."""
    options = ", ".join(f"{key} {value}" for key, value in choices.items())
    while True:
        answer = ask(f"{prompt} ({options})")
        if answer in choices:
            return choices[answer]
        print("Choose one of the listed options.")


def ask_lines() -> list[Line]:
    """Ask for (product, condition, quantity) lines until the product is blank."""
    lines = []
    while True:
        product_id = ask_int("Product id (blank to finish)", optional=True)
        if product_id is None:
            return lines
        condition = ask_choice("Condition", CONDITIONS)
        lines.append((product_id, condition, ask_int("Quantity")))


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


def new_customer(conn: sqlite3.Connection) -> None:
    """Add a customer and print the new customer id."""
    customer_id = services.add_customer(
        conn, ask("First name"), ask("Last name"), ask("Phone (10 digits)")
    )
    print(f"Added customer {customer_id}.")


def enroll_member(conn: sqlite3.Connection) -> None:
    """Enroll an existing customer in the loyalty program for one year."""
    customer_id = ask_int("Customer id")
    services.add_member(conn, customer_id, email=ask("Email (optional)") or None)
    print(f"Enrolled customer {customer_id} for one year.")


def sell(conn: sqlite3.Connection) -> None:
    """Record a sale and print its total (sale_total view)."""
    lines = ask_lines()
    member_id = ask_int("Member customer id (blank if none)", optional=True)
    payment = ask_choice("Payment", PAYMENTS)
    sale_id = services.record_sale(conn, lines, payment, member_id)
    rows = conn.execute(
        "SELECT sale_id, item_count, subtotal_cents, discount_cents, total_cents "
        "FROM sale_total WHERE sale_id = ?",
        (sale_id,),
    ).fetchall()
    show(("Sale", "Items", "Subtotal", "Discount", "Total"), rows, money=(2, 3, 4))


def trade(conn: sqlite3.Connection) -> None:
    """Record a trade-in and print the payout (trade_in_total view)."""
    customer_id = ask_int("Customer id")
    trade_in_id = services.record_trade_in(conn, customer_id, ask_lines())
    rows = conn.execute(
        "SELECT trade_in_id, item_count, payout_cents FROM trade_in_total "
        "WHERE trade_in_id = ?",
        (trade_in_id,),
    ).fetchall()
    show(("Trade-in", "Items", "Payout"), rows, money=(2,))


# ----- Manager -----


def low_stock(conn: sqlite3.Connection) -> None:
    """List stock at or below its reorder threshold (manager_low_stock view)."""
    rows = conn.execute(
        "SELECT product_id, name, condition, qty_on_hand, reorder_threshold "
        "FROM manager_low_stock ORDER BY product_id, condition"
    ).fetchall()
    show(("ID", "Name", "Condition", "Qty", "Reorder at"), rows)


def members(conn: sqlite3.Connection) -> None:
    """List loyalty members and whether each is active today (member_status view)."""
    rows = conn.execute(
        "SELECT customer_id, first_name, last_name, join_date, expiry_date, "
        "CASE WHEN is_active THEN 'yes' ELSE 'no' END "
        "FROM member_status ORDER BY customer_id"
    ).fetchall()
    show(("ID", "First", "Last", "Joined", "Expires", "Active"), rows)


def purchases(conn: sqlite3.Connection) -> None:
    """Count each member's purchases in a period (Q2)."""
    start, end = ask_date("Start"), ask_date("End (not included)")
    rows = queries.purchases_per_member(conn, start, end)
    show(("ID", "First", "Last", "Purchases"), rows)


def above_average(conn: sqlite3.Connection) -> None:
    """List used games priced above the average for their condition (Q4)."""
    rows = queries.used_games_above_average(conn)
    show(("Name", "Platform", "Condition", "Price"), rows, money=(3,))


def every_type(conn: sqlite3.Connection) -> None:
    """List members who bought a game, a console, and an accessory (Q5)."""
    show(("ID", "First", "Last"), queries.members_who_bought_every_type(conn))


def stale_stock(conn: sqlite3.Connection) -> None:
    """List in-stock products with no recent sale (Q6)."""
    days = ask_int("Days without a sale")
    rows = queries.products_without_recent_sales(conn, date.today().isoformat(), days)
    show(("ID", "Name", "Type"), rows)


# ----- Analyst -----


def sale_lines(conn: sqlite3.Connection) -> None:
    """List every sale line (analyst_sale_lines view)."""
    rows = conn.execute(
        "SELECT sale_id, sale_datetime, name, condition, quantity, "
        "unit_price_cents, discount_amount_cents, line_total_cents "
        "FROM analyst_sale_lines ORDER BY sale_id, product_id"
    ).fetchall()
    headers = ("Sale", "Date", "Name", "Condition", "Qty", "Price", "Discount", "Total")
    show(headers, rows, money=(5, 6, 7))


def platform_sales(conn: sqlite3.Connection) -> None:
    """List platforms that sold at least a number of game units in a period (Q3)."""
    start, end = ask_date("Start"), ask_date("End (not included)")
    rows = queries.platforms_with_game_sales(conn, start, end, ask_int("Minimum units"))
    show(("Platform", "Units"), rows)


def sale_totals(conn: sqlite3.Connection) -> None:
    """List every sale with its totals (sale_total view)."""
    rows = conn.execute(
        "SELECT sale_id, sale_datetime, payment_method, item_count, "
        "subtotal_cents, discount_cents, total_cents FROM sale_total ORDER BY sale_id"
    ).fetchall()
    headers = ("Sale", "Date", "Payment", "Items", "Subtotal", "Discount", "Total")
    show(headers, rows, money=(4, 5, 6))


# ----- Menus -----

Action = Callable[[sqlite3.Connection], None]

# Each role's menu maps the key to type to (label, function to call).
MENUS: dict[str, dict[str, tuple[str, Action]]] = {
    "clerk": {
        "1": ("Stock list", stock),
        "2": ("Games in stock for a platform", games_on_platform),
        "3": ("Look up a customer", lookup_customer),
        "4": ("Add a customer", new_customer),
        "5": ("Enroll a loyalty member", enroll_member),
        "6": ("Record a sale", sell),
        "7": ("Record a trade-in", trade),
    },
    "manager": {
        "1": ("Low stock", low_stock),
        "2": ("Loyalty members", members),
        "3": ("Purchases per member", purchases),
        "4": ("Used games above average price", above_average),
        "5": ("Members who bought every type", every_type),
        "6": ("Products without recent sales", stale_stock),
    },
    "analyst": {
        "1": ("Sale lines", sale_lines),
        "2": ("Game units sold by platform", platform_sales),
        "3": ("Sale totals", sale_totals),
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
