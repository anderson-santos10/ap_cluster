"""Busca global somente leitura de itens e entregas.

A consulta é normalizada para comparar. Os registros gravados não mudam.
"""

from django.db.models import CharField, Q
from django.db.models.functions import Cast
from django.urls import reverse

from criticals.models import CriticalItem, Delivery

MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 80
RESULT_LIMIT = 8


def parse_query(raw):
    """Classifica o texto digitado sem alterar o banco.

    Espaço nas pontas sai só da consulta. O código gravado permanece.
    """

    text = "" if raw is None else str(raw)
    if len(text) > MAX_QUERY_LENGTH:
        return "", "long"
    term = text.strip()
    if len(term) < MIN_QUERY_LENGTH:
        return term, "short"
    return term, "ok"


def global_search(user, term):
    groups = []
    if user.has_perm("criticals.view_criticalitem"):
        groups.append(_item_group(term))
        if user.has_perm("criticals.view_delivery"):
            groups.append(_delivery_group(term))
    return groups


def _item_group(term):
    items = (
        CriticalItem.objects.filter(_item_match(term))
        .order_by("material", "center")[:RESULT_LIMIT]
    )
    return {
        "category": "itens",
        "label": "Itens críticos",
        "results": [_item_result(item) for item in items],
    }


def _delivery_group(term):
    deliveries = (
        Delivery.objects.select_related("item")
        .annotate(
            quantity_text=Cast("quantity", CharField()),
            delivered_text=Cast("delivered_on", CharField()),
        )
        .filter(_delivery_match(term))
        .order_by("item__material", "item__center", "pk")[:RESULT_LIMIT]
    )
    return {
        "category": "entregas",
        "label": "Entregas",
        "results": [_delivery_result(delivery) for delivery in deliveries],
    }


def _item_match(term, prefix=""):
    def lookup(field):
        return f"{prefix}{field}__icontains"

    return (
        Q(**{lookup("material"): term})
        | Q(**{lookup("description"): term})
        | Q(**{lookup("center"): term})
        | Q(**{lookup("status"): term})
        | Q(**{lookup("observation"): term})
    )


def _delivery_match(term):
    return (
        _item_match(term, "item__")
        | Q(source__icontains=term)
        | Q(quantity_text__icontains=term)
        | Q(delivered_text__icontains=term)
    )


def _item_result(item):
    status = item.status or "status ausente"
    meta = f"{item.center} · {status}"
    if item.material != item.material.strip():
        meta = f"espaço preservado · {meta}"
    return {
        "type": "item",
        "title": item.material,
        "detail": _brief(item.description),
        "meta": meta,
        "url": reverse("critical-item-detail", args=[item.pk]),
    }


def _delivery_result(delivery):
    item = delivery.item
    when = delivery.delivered_on.strftime("%d/%m/%Y") if delivery.delivered_on else "data ausente"
    return {
        "type": "entrega",
        "title": item.material,
        "detail": _brief(item.description),
        "meta": f"{item.center} · {_quantity_label(delivery.quantity)} · {when}",
        "url": reverse("critical-item-detail", args=[item.pk]) + f"#entrega-{delivery.pk}",
    }


def _brief(text):
    value = "" if text is None else str(text)
    if len(value) <= 140:
        return value
    return value[:139].rstrip() + "…"


def _quantity_label(value):
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text
