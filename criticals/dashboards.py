"""Indicadores dos dashboards a partir dos registros já gravados.

Não soma estoque, não trata ausência como zero e não calcula saldo pendente.
"""

from django.db.models import Count, F, Q
from django.db.models.functions import TruncMonth
from django.urls import reverse

from criticals.models import Delivery, StockPosition
from criticals.panel import _percent, _width, month_label, parse_month, status_sort_key
from criticals.stock import annotate_positions, format_quantity


def attention(items):
    """Revisão já definida nas regras: negativa, data ausente, literal e status ausente."""
    deliveries = Delivery.objects.filter(item__in=items)
    negatives = list(
        deliveries.filter(quantity__lt=0)
        .select_related("item")
        .order_by("item__material", "item__center", "pk")
    )
    missing_dates = list(
        deliveries.filter(delivered_on__isnull=True)
        .select_related("item")
        .order_by("item__material", "item__center", "pk")
    )
    literals = list(
        items.filter(forecast_on__isnull=True)
        .exclude(forecast_original="")
        .order_by("material", "center")
    )
    absent = list(items.filter(status="").order_by("material", "center"))
    rows = []
    for delivery in negatives:
        rows.append(_delivery_attention(delivery, "Quantidade negativa"))
    for delivery in missing_dates:
        rows.append(_delivery_attention(delivery, "Data de entrega ausente"))
    for item in literals:
        rows.append(
            {
                "reason": "Previsão literal, sem data",
                "material": item.material,
                "center": item.center,
                "detail": item.forecast_original,
                "url": _item_url(item.pk),
            }
        )
    for item in absent:
        rows.append(
            {
                "reason": "Status ausente",
                "material": item.material,
                "center": item.center,
                "detail": "ausente",
                "url": _item_url(item.pk),
            }
        )
    return {
        "negative": len(negatives),
        "missing_dates": len(missing_dates),
        "literals": len(literals),
        "absent_status": len(absent),
        "rows": rows,
    }


def stock_report(items):
    item_count = items.count()
    positions = list(
        StockPosition.objects.filter(item__in=items)
        .select_related("item")
        .order_by("material", "center", "deposit", "lot", "pk")
    )
    rows, repeated_groups = annotate_positions(positions)
    covered = {row["item_pk"] for row in rows}
    unknown_items = list(
        items.exclude(pk__in=covered).order_by("material", "center")[:40]
    ) if covered else list(items.order_by("material", "center")[:40])
    return {
        "item_count": item_count,
        "with_position": len(covered),
        "unknown": item_count - len(covered),
        "unknown_items": unknown_items,
        "position_count": len(rows),
        "repeated_groups": repeated_groups,
        "divergences": sum(1 for row in rows if row["description_differs"]),
        "decimal_pc": sum(1 for row in rows if row["decimal_pc"]),
        "rows": rows,
    }


def delivery_report(items, month_param):
    base = Delivery.objects.filter(item__in=items)
    totals = base.aggregate(
        total=Count("id"),
        dated=Count("id", filter=Q(delivered_on__isnull=False)),
        undated=Count("id", filter=Q(delivered_on__isnull=True)),
        negative=Count("id", filter=Q(quantity__lt=0)),
    )
    months = list(
        base.filter(delivered_on__isnull=False)
        .values(month_start=TruncMonth("delivered_on"))
        .annotate(count=Count("id"))
        .order_by("month_start")
    )
    peak = max((row["count"] for row in months), default=0)
    for row in months:
        start = row["month_start"]
        row["label"] = month_label(start.year, start.month)
        row["value"] = f"{start.year:04d}-{start.month:02d}"
        row["width"] = _width(row["count"], peak)
    line = _line(months)
    selected = parse_month(month_param)
    scoped = base
    selected_label = ""
    selected_value = ""
    if selected:
        year, month = selected
        scoped = base.filter(delivered_on__year=year, delivered_on__month=month)
        selected_label = month_label(year, month)
        selected_value = f"{year:04d}-{month:02d}"
    scoped_total = scoped.count() if selected else totals["total"]
    statuses = list(scoped.values(status=F("item__status")).annotate(count=Count("id")))
    statuses.sort(key=lambda row: status_sort_key(row["status"] or ""))
    for row in statuses:
        row["label"] = row["status"] or "ausente"
        row["percent"], row["percent_label"] = _percent(row["count"], scoped_total)
        row["width"] = _width(row["count"], scoped_total)
    rows = []
    for delivery in scoped.select_related("item").order_by(
        "item__material",
        "item__center",
        "pk",
    ):
        rows.append(
            {
                "material": delivery.item.material,
                "center": delivery.item.center,
                "status": delivery.item.status or "ausente",
                "quantity": format_quantity(delivery.quantity),
                "negative": delivery.quantity < 0,
                "date_label": (
                    delivery.delivered_on.strftime("%d/%m/%Y")
                    if delivery.delivered_on
                    else "ausente"
                ),
                "url": _item_url(delivery.item_id, f"entrega-{delivery.pk}"),
            }
        )
    return {
        "total": totals["total"],
        "dated": totals["dated"],
        "undated": totals["undated"],
        "negative": totals["negative"],
        "months": months,
        "line": line,
        "selected_label": selected_label,
        "selected_value": selected_value,
        "scoped_total": scoped_total,
        "statuses": statuses,
        "rows": rows,
    }


def _line(months):
    if len(months) < 2:
        return ""
    peak = max(row["count"] for row in months)
    last = len(months) - 1
    coords = []
    for index, row in enumerate(months):
        x = 6 + (88 * index / last)
        y = 38 - (30 * row["count"] / peak)
        row["x"] = f"{x:.2f}"
        row["y"] = f"{y:.2f}"
        coords.append(f"{row['x']},{row['y']}")
    return " ".join(coords)


def _item_url(pk, fragment=""):
    url = reverse("critical-item-detail", args=[pk])
    if fragment:
        return f"{url}#{fragment}"
    return url


def _delivery_attention(delivery, reason):
    detail = format_quantity(delivery.quantity)
    if delivery.delivered_on is None and reason == "Data de entrega ausente":
        detail = f"{detail}, sem data"
    return {
        "reason": reason,
        "material": delivery.item.material,
        "center": delivery.item.center,
        "detail": detail,
        "url": _item_url(delivery.item_id, f"entrega-{delivery.pk}"),
    }
