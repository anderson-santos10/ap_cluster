from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView

from criticals.codes import material_collisions, spacing_items
from criticals.dashboards import attention, delivery_report, stock_report
from criticals.forms import DeliveryForm, ItemFilterForm, PanelFilterForm, StatusForm
from criticals.models import CriticalItem, Delivery, StatusChange
from criticals.panel import (
    ABSENT_STATUS,
    apply_item_filters,
    extra_filter_notes,
    summarize,
    without_extra_filters,
)
from criticals.preparation import normalized_code
from criticals.search import global_search, parse_query
from criticals.stock import position_rows


class GlobalSearchView(View):
    """Consulta JSON de itens e entregas. Não grava nem altera registros."""

    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Autenticação necessária."}, status=401)
        term, state = parse_query(request.GET.get("q", ""))
        if state == "long":
            return JsonResponse(
                {"error": "A consulta pode ter no máximo 80 caracteres."},
                status=400,
            )
        if state == "short":
            return JsonResponse(
                {
                    "query": term,
                    "groups": [],
                    "message": "Digite ao menos 2 caracteres.",
                }
            )
        return JsonResponse(
            {"query": term, "groups": global_search(request.user, term)},
            json_dumps_params={"ensure_ascii": False},
        )


class ItemQueryMixin:
    def filtered_items(self):
        form = ItemFilterForm(self.request.GET or None)
        if form.is_valid():
            items = apply_item_filters(self.request.GET, form.cleaned_data)
        else:
            items = CriticalItem.objects.all().order_by("material", "center")
        return form, items


class CriticalItemListView(LoginRequiredMixin, PermissionRequiredMixin, ItemQueryMixin, ListView):
    permission_required = "criticals.view_criticalitem"
    template_name = "criticals/item_list.html"
    context_object_name = "items"
    paginate_by = 25

    def get_queryset(self):
        _form, items = self.filtered_items()
        return items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form, _items = self.filtered_items()
        context["filter_form"] = form
        query = self.request.GET.copy()
        query.pop("page", None)
        context["filter_query"] = query.urlencode()
        context["extra_filters"] = extra_filter_notes(self.request.GET)
        context["filters_without_extra"] = without_extra_filters(self.request.GET)
        context["collisions"] = material_collisions()
        context["spacing_count"] = len(spacing_items())
        return context


class CriticalItemDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = "criticals.view_criticalitem"
    model = CriticalItem
    template_name = "criticals/item_detail.html"
    context_object_name = "item"

    def get_queryset(self):
        return CriticalItem.objects.prefetch_related(
            "deliveries",
            "status_changes",
            "stock_positions",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = context["item"]
        normalized = normalized_code(item.material)
        context["normalized_material"] = normalized
        context["has_extra_space"] = item.material != normalized
        context["collisions"] = [
            collision
            for collision in material_collisions()
            if collision["normalizado"] == normalized
        ]
        context["lrr_absent"] = item.lrr is None
        context["stock_rows"] = position_rows(item)
        return context


class PanelView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "criticals.view_criticalitem"
    template_name = "criticals/panel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form, valid, items, base, filter_query = _dashboard_filter(self.request)
        summary = summarize(items)
        _attach_links(summary, base)
        context.update(_dashboard_common(form, filter_query, "critical-panel", "executivo"))
        context["summary"] = summary
        context["attention"] = attention(items) if valid else _empty_attention()
        context["filtered_list_url"] = _list_href(base)
        return context


class StockDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "criticals.view_criticalitem"
    template_name = "criticals/stock_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form, valid, items, base, filter_query = _dashboard_filter(self.request)
        report = stock_report(items) if valid else _empty_stock()
        context.update(_dashboard_common(form, filter_query, "critical-stock-dashboard", "estoque"))
        context["report"] = report
        context["page"] = _page(report["rows"], self.request.GET.get("page"))
        context["page_query"] = _page_query(base)
        return context


class DeliveryDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "criticals.view_criticalitem"
    template_name = "criticals/delivery_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form, valid, items, base, filter_query = _dashboard_filter(self.request)
        report = delivery_report(items, self.request.GET.get("entrega")) if valid else _empty_delivery()
        month_base = dict(base)
        for row in report["months"]:
            row["list_url"] = _self_href("critical-delivery-dashboard", {**month_base, "entrega": row["value"]})
        for row in report["statuses"]:
            params = {key: value for key, value in month_base.items() if key not in {"status", "status_ausente"}}
            if report["selected_value"]:
                params["entrega"] = report["selected_value"]
            if row["status"]:
                params["status"] = row["status"]
            else:
                params["status_ausente"] = "1"
            row["list_url"] = _self_href("critical-delivery-dashboard", params)
        summary = summarize(items)
        _attach_links(summary, base)
        context.update(
            _dashboard_common(form, filter_query, "critical-delivery-dashboard", "entregas")
        )
        context["summary"] = summary
        context["report"] = report
        context["page"] = _page(report["rows"], self.request.GET.get("page"))
        context["page_query"] = _page_query({**base, "entrega": report["selected_value"]})
        return context


def _dashboard_filter(request):
    centers = list(
        CriticalItem.objects.order_by("center").values_list("center", flat=True).distinct()
    )
    statuses = list(
        CriticalItem.objects.order_by("status").values_list("status", flat=True).distinct()
    )
    incoming = request.GET
    if incoming:
        form = PanelFilterForm(incoming, centers=centers, statuses=statuses)
        valid = form.is_valid()
        cleaned = form.cleaned_data if valid else {}
    else:
        form = PanelFilterForm(centers=centers, statuses=statuses)
        valid = True
        cleaned = {"centro": "", "status": ""}
    if valid:
        items = apply_item_filters(incoming, cleaned)
    else:
        items = CriticalItem.objects.none()
    base = _panel_params(cleaned if valid else {})
    return form, valid, items, base, urlencode(base)


def _dashboard_common(form, filter_query, clear_name, current):
    return {
        "filter_form": form,
        "filter_query": filter_query,
        "clear_url": reverse(clear_name),
        "current": current,
    }


def _empty_attention():
    return {"negative": 0, "missing_dates": 0, "literals": 0, "absent_status": 0, "rows": []}


def _empty_stock():
    return {
        "item_count": 0,
        "with_position": 0,
        "unknown": 0,
        "unknown_items": [],
        "position_count": 0,
        "repeated_groups": 0,
        "divergences": 0,
        "decimal_pc": 0,
        "rows": [],
    }


def _empty_delivery():
    return {
        "total": 0,
        "dated": 0,
        "undated": 0,
        "negative": 0,
        "months": [],
        "line": "",
        "selected_label": "",
        "selected_value": "",
        "scoped_total": 0,
        "statuses": [],
        "rows": [],
    }


def _page(rows, number):
    return Paginator(rows, 25).get_page(number)


def _page_query(params):
    clean = {key: value for key, value in params.items() if value}
    query = urlencode(clean)
    if query:
        return query + "&"
    return ""


def _self_href(name, params):
    clean = {key: value for key, value in params.items() if value}
    query = urlencode(clean)
    url = reverse(name)
    if query:
        return f"{url}?{query}"
    return url


def _panel_params(cleaned):
    params = {}
    center = cleaned.get("centro") or ""
    status = cleaned.get("status") or ""
    if center:
        params["centro"] = center
    if status == ABSENT_STATUS:
        params["status_ausente"] = "1"
    elif status:
        params["status"] = status
    return params


def _list_href(params):
    clean = {key: value for key, value in params.items() if value}
    query = urlencode(clean)
    url = reverse("critical-item-list")
    if query:
        return f"{url}?{query}"
    return url


def _attach_links(summary, base):
    summary["total_url"] = _list_href(base)
    summary["dated_url"] = _list_href({**base, "com_previsao": "1"})
    summary["undated_url"] = _list_href({**base, "sem_previsao": "1"})
    for row in summary["centers"]:
        row["list_url"] = _list_href({**base, "centro": row["center"]})
    for row in summary["statuses"]:
        params = {key: value for key, value in base.items() if key not in {"status", "status_ausente"}}
        if row["status"]:
            params["status"] = row["status"]
        else:
            params["status_ausente"] = "1"
        row["list_url"] = _list_href(params)
    for row in summary["months"]:
        params = {
            key: value
            for key, value in base.items()
            if key not in {"previsao", "sem_previsao", "com_previsao"}
        }
        params["previsao"] = row["value"]
        row["list_url"] = _list_href(params)


class InconsistencyView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = "criticals.view_criticalitem"
    template_name = "criticals/inconsistencies.html"
    context_object_name = "spacing"
    paginate_by = 25

    def get_queryset(self):
        return spacing_items()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["collisions"] = material_collisions()
        context["negative_deliveries"] = Delivery.objects.filter(
            quantity__lt=0
        ).select_related("item")
        context["missing_dates"] = Delivery.objects.filter(
            delivered_on__isnull=True
        ).select_related("item")
        context["literal_forecasts"] = CriticalItem.objects.exclude(forecast_original="")
        return context


class DeliveryCreateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = "criticals.add_delivery"
    form_class = DeliveryForm
    template_name = "criticals/delivery_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.item = get_object_or_404(CriticalItem, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item"] = self.item
        return context

    def form_valid(self, form):
        delivery = form.save(commit=False)
        delivery.item = self.item
        delivery.author = self.request.user
        delivery.source = ""
        delivery.source_row = None
        delivery.save()
        if delivery.requires_review:
            messages.warning(
                self.request,
                "Entrega registrada. A quantidade negativa foi preservada para revisão.",
            )
        else:
            messages.success(self.request, "Entrega registrada.")
        return redirect("critical-item-detail", pk=self.item.pk)


class StatusChangeView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = "criticals.change_critical_status"
    form_class = StatusForm
    template_name = "criticals/status_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.item = get_object_or_404(CriticalItem, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item"] = self.item
        return context

    def form_valid(self, form):
        previous = self.item.status
        if previous:
            StatusChange.objects.create(
                item=self.item,
                status=previous,
                changed_by=self.request.user,
                changed_at=timezone.now(),
            )
        self.item.status = form.cleaned_data["status"]
        self.item.save(update_fields=["status"])
        messages.success(self.request, "Status atualizado. O valor anterior permanece no histórico.")
        return redirect("critical-item-detail", pk=self.item.pk)
