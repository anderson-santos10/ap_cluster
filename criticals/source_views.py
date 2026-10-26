"""Consultas autenticadas, somente leitura, das linhas-fonte vinculadas."""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.views.generic import TemplateView

from criticals.forms import ItemFilterForm
from criticals.models import CriticalItem, LinkedSheetRow
from criticals.panel import apply_item_filters


SOURCE_PAGES = {
    "SQVI": {
        "title": "Documentos SQVI",
        "current": "sqvi",
        "template": "criticals/sqvi_dashboard.html",
        "columns": (
            ("T", "Material (T)"),
            ("R", "Cen. (R)"),
            ("H", "Tipo (H)"),
            ("J", "Doc.compra (J)"),
            ("K", "Item (K)"),
            ("L", "Fornecedor (L)"),
            ("V", "Qtd.pedido (V)"),
            ("W", "UMP (W)"),
        ),
        "intro": (
            "Linhas da aba SQVI ligadas somente por material e centro exatos. "
            "A tabela mantém documentos distintos e não calcula recebimentos "
            "nem saldo pendente."
        ),
    },
    "LRR": {
        "title": "Parâmetros LRR",
        "current": "lrr",
        "template": "criticals/lrr_dashboard.html",
        "columns": (
            ("B", "Material (B)"),
            ("D", "Área MRP centro (D)"),
            ("F", "Tipo de MRP (F)"),
            ("G", "Planejador MRP (G)"),
            ("H", "Grupo MRP (H)"),
            ("I", "Ponto reabastec. (I)"),
            ("J", "Ciclo MRP (J)"),
            ("L", "Tamanho do lote MRP (L)"),
        ),
        "intro": (
            "Linhas da aba LRR ligadas somente por material e Área MRP centro "
            "exatos. Os parâmetros permanecem como dados da fonte e não "
            "substituem o LRR informado no item crítico."
        ),
    },
}


class LinkedSourceRowsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Apresenta linhas importadas sem reinterpretar os campos da planilha."""

    permission_required = "criticals.view_criticalitem"
    sheet = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_info = SOURCE_PAGES[self.sheet]
        form = ItemFilterForm(self.request.GET or None)
        filters_valid = form.is_valid()
        if filters_valid:
            items = apply_item_filters(self.request.GET, form.cleaned_data)
        else:
            items = CriticalItem.objects.none()

        source_rows = LinkedSheetRow.objects.filter(
            sheet=self.sheet,
            item__in=items,
        ).select_related("item").order_by(
            "item__material",
            "item__center",
            "source_row",
        )
        row_count = source_rows.count()
        linked_item_ids = source_rows.values_list("item_id", flat=True).distinct()
        matching_items = items.count()
        missing_item_count = items.exclude(pk__in=linked_item_ids).count()
        linked_item_count = source_rows.values("item_id").distinct().count()

        page = Paginator(source_rows, 25).get_page(self.request.GET.get("page"))
        columns = page_info["columns"]
        records = [
            _present_record(row, columns)
            for row in page.object_list
        ]
        query = self.request.GET.copy()
        query.pop("page", None)
        context.update(
            {
                "title": page_info["title"],
                "intro": page_info["intro"],
                "current": page_info["current"],
                "filter_form": form,
                "filter_query": query.urlencode(),
                "page_query": query.urlencode(),
                "page": page,
                "columns": [
                    {"letter": letter, "label": label}
                    for letter, label in columns
                ],
                "records": records,
                "row_count": row_count,
                "matching_items": matching_items,
                "linked_item_count": linked_item_count,
                "missing_item_count": missing_item_count,
                "filters_invalid": not filters_valid,
            }
        )
        return context


class SQVIDashboardView(LinkedSourceRowsView):
    template_name = SOURCE_PAGES["SQVI"]["template"]
    sheet = "SQVI"


class LRRDashboardView(LinkedSourceRowsView):
    template_name = SOURCE_PAGES["LRR"]["template"]
    sheet = "LRR"


def _present_record(record, columns):
    raw_by_letter = {cell["column"]: cell for cell in record.raw_values}
    visible_values = [
        _display_value(raw_by_letter.get(letter, {}))
        for letter, _label in columns
    ]
    details = []
    for cell in record.raw_values:
        value = cell.get("value")
        if "formula" in cell:
            formula = cell["formula"]
            cached = cell.get("cached_value", {}).get("value")
            display = f"Fórmula: {formula}; cache da planilha: {_as_text(cached)}"
        else:
            display = _as_text(value.get("value") if value else None)
        header = cell.get("header") or "Coluna sem cabeçalho"
        details.append(
            {
                "label": f"{header} ({cell['column']})",
                "value": display,
            }
        )
    return {
        "source_row": record.source_row,
        "item": record.item,
        "visible_values": visible_values,
        "details": details,
    }


def _display_value(cell):
    value = cell.get("value")
    if value is None:
        return "—"
    return _as_text(value.get("value"))


def _as_text(value):
    if value is None or value == "":
        return "em branco"
    return str(value)
