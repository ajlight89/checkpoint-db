"""Money amounts, kept as whole cents so that no rounding error builds up."""

# BR-21: an active loyalty member receives this percentage off each sale line.
MEMBER_DISCOUNT_PERCENT = 10


def percent_of(cents: int, percent: int) -> int:
    """Return ``percent`` percent of ``cents``, rounded half up to a whole cent.

    Integer arithmetic only: adding 50 before dividing by 100 rounds a
    half cent up, so 10% of 1245 cents is 125, not 124.
    """
    if cents < 0 or percent < 0:
        raise ValueError("cents and percent must not be negative")
    return (cents * percent + 50) // 100


def member_discount(line_cents: int) -> int:
    """Return the member discount on a sale line worth ``line_cents``."""
    return percent_of(line_cents, MEMBER_DISCOUNT_PERCENT)


def format_cents(cents: int) -> str:
    """Show an amount in dollars, such as ``$1,234.56`` or ``-$2.50``."""
    sign = "-" if cents < 0 else ""
    dollars, remainder = divmod(abs(cents), 100)
    return f"{sign}${dollars:,}.{remainder:02d}"
