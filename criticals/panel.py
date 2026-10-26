"""Contagens do painel a partir dos itens já gravados.

Os percentuais nascem aqui. Cache de gráfico e tabela dinâmica não entram.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth

from criticals.models import CriticalItem

ABSENT_STATUS = "__ausente__"
STATUS_ORDER = (
    "Em rota",
    "Pendente",
    "Entregue",
    "Entregue parcial",
    "Criar RC",
    "Sem necessidade parque",
    "Obsoleto",
)
_MONTHS = (
    "",
    "JAN",
    "FEV",
    "MAR",
    "ABR",
    "MAI",
    "JUN",
    "JUL",
    "AGO",
    "SET",
    "OUT",
    "NOV",
    "DEZ",
)
_EXTRA_KEYS = ("status_ausente", "previsao", "sem_previsao", "com_previsao")


def parse_month(value):
    text = "" if value is None else str(value).strip()
    if len(text) != 7 or text[4] != "-":
        return None
    year_text, month_text = text[:4], text[5:]
    if not (year_text.isdigit() and month_text.isdigit()):
        return None
    year, month = int(year_text), int(month_text)
    try:
        date(year, month, 1)
    except ValueError:
        return None
    return year, month


def month_label(year, month):
    return f"{_MONTHS[month]}/{year}"


def _flag(params, key):
    return str(params.get(key, "")).strip() == "1"


def _percent(count, whole):
    if not whole:
        return None, ""
    value = (Decimal(count) * Decimal(100) / Decimal(whole)).quantize(
        Decimal("0.1"),
        rounding=ROUND_HALF_UP,
    )
    label = f"{value:.1f}".replace(".", ",") + "%"
    return value, label


def _width(count, whole):
    if not count or not whole:
        return "0"
    ratio = Decimal(count) * Decimal(100) / Decimal(whole)
    if ratio < Decimal("0.4"):
        return "0.4"
    return format(ratio.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP), "f")


def status_sort_key(status):
    if status in STATUS_ORDER:
        return (0, STATUS_ORDER.index(status))
    if status == "":
        return (2, "")
    return (1, status)


def apply_item_filters(params, cleaned):
    """Filtra a consulta da lista e do painel sem gravar nada.

    Material e descrição continuam parciais. Centro e status são exatos,
    para que Entregue não arraste Entregue parcial.
    """

    items = CriticalItem.objects.all()
    material = cleaned.get("material") or ""
    description = cleaned.get("descricao") or ""
    center = cleaned.get("centro") or ""
    status = cleaned.get("status") or ""
    if material:
        items = items.filter(material__icontains=material)
    if description:
        items = items.filter(description__icontains=description)
    if center:
        items = items.filter(center=center)
    if status == ABSENT_STATUS or (not status and _flag(params, "status_ausente")):
        items = items.filter(status="")
    elif status:
        items = items.filter(status=status)
    if _flag(params, "sem_previsao"):
        items = items.filter(forecast_on__isnull=True)
    elif _flag(params, "com_previsao"):
        items = items.filter(forecast_on__isnull=False)
    else:
        parsed = parse_month(params.get("previsao"))
        if parsed:
            year, month = parsed
            items = items.filter(forecast_on__year=year, forecast_on__month=month)
    return items.order_by("material", "center")


def extra_filter_notes(params):
    notes = []
    if _flag(params, "status_ausente"):
        notes.append({"name": "status_ausente", "value": "1", "label": "Status ausente"})
    if _flag(params, "sem_previsao"):
        notes.append({"name": "sem_previsao", "value": "1", "label": "Sem data válida"})
    elif _flag(params, "com_previsao"):
        notes.append({"name": "com_previsao", "value": "1", "label": "Com data válida"})
    else:
        parsed = parse_month(params.get("previsao"))
        if parsed:
            year, month = parsed
            notes.append(
                {
                    "name": "previsao",
                    "value": f"{year:04d}-{month:02d}",
                    "label": month_label(year, month),
                }
            )
    return notes


def without_extra_filters(params):
    query = params.copy()
    for key in _EXTRA_KEYS:
        query.pop(key, None)
    query.pop("page", None)
    return query.urlencode()


def summarize(queryset):
    # A ordenação da lista entra no agrupamento. Aqui a conta é por categoria.
    queryset = queryset.order_by()
    totals = queryset.aggregate(
        total=Count("id"),
        dated=Count("id", filter=Q(forecast_on__isnull=False)),
        undated=Count("id", filter=Q(forecast_on__isnull=True)),
    )
    total = totals["total"]
    dated = totals["dated"]
    centers = list(queryset.values("center").annotate(count=Count("id")).order_by("center"))
    peak = max((row["count"] for row in centers), default=0)
    for row in centers:
        row["label"] = row["center"]
        row["width"] = _width(row["count"], peak)
    statuses = list(queryset.values("status").annotate(count=Count("id")))
    statuses.sort(key=lambda row: status_sort_key(row["status"]))
    for row in statuses:
        row["label"] = row["status"] or "ausente"
        row["percent"], row["percent_label"] = _percent(row["count"], total)
        row["width"] = _width(row["count"], total)
    months = list(
        queryset.filter(forecast_on__isnull=False)
        .values(month_start=TruncMonth("forecast_on"))
        .annotate(count=Count("id"))
        .order_by("month_start")
    )
    for row in months:
        start = row["month_start"]
        row["label"] = month_label(start.year, start.month)
        row["value"] = f"{start.year:04d}-{start.month:02d}"
        row["percent"], row["percent_label"] = _percent(row["count"], dated)
        row["width"] = _width(row["count"], dated)
    literals = list(
        queryset.filter(forecast_on__isnull=True)
        .exclude(forecast_original="")
        .values("forecast_original")
        .annotate(count=Count("id"))
        .order_by("forecast_original")
    )
    return {
        "total": total,
        "dated": dated,
        "undated": totals["undated"],
        "centers": centers,
        "statuses": statuses,
        "months": months,
        "literals": literals,
        "center_count": len(centers),
    }
