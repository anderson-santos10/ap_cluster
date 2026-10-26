"""Apresentação das posições de estoque já ligadas a um item.

Não soma quantidades, não remove espaço e não altera o item.
"""

from collections import Counter
from decimal import Decimal


def position_rows(item):
    positions = list(item.stock_positions.all())
    counts = Counter((row.deposit, row.lot) for row in positions)
    return [_row(item, position, counts) for position in positions]


def annotate_positions(positions):
    """Marca repetição dentro do mesmo item. Não soma quantidades."""
    counts = Counter((position.item_id, position.deposit, position.lot) for position in positions)
    rows = []
    for position in positions:
        size = counts[(position.item_id, position.deposit, position.lot)]
        local = Counter({(position.deposit, position.lot): size})
        row = _row(position.item, position, local)
        row["material"] = position.material
        row["center"] = position.center
        row["item_pk"] = position.item_id
        rows.append(row)
    repeated_groups = sum(1 for size in counts.values() if size > 1)
    return rows, repeated_groups


def _row(item, position, counts):
    quantities = (
        position.unrestricted,
        position.in_transit,
        position.in_quality,
        position.blocked,
    )
    return {
        "deposit_label": _blank(position.deposit),
        "deposit_description": position.deposit_description,
        "lot_label": _blank(position.lot),
        "center_name": position.center_name,
        "unit": position.unit,
        "unrestricted": _quantity(position.unrestricted),
        "in_transit": _quantity(position.in_transit),
        "in_quality": _quantity(position.in_quality),
        "blocked": _quantity(position.blocked),
        "repeated": counts[(position.deposit, position.lot)] > 1,
        "decimal_pc": position.unit == "PC" and any(_fractional(value) for value in quantities),
        "description_differs": position.stock_description != item.description,
        "stock_description": position.stock_description,
    }


def _blank(value):
    text = "" if value is None else str(value)
    if text == "":
        return "em branco"
    return text


def _fractional(value):
    number = Decimal(value)
    return number != number.to_integral_value()


def format_quantity(value):
    text = format(Decimal(value), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _quantity(value):
    return format_quantity(value)
