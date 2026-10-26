from django.urls import path

from criticals.views import (
    CriticalItemDetailView,
    CriticalItemListView,
    DeliveryCreateView,
    GlobalSearchView,
    InconsistencyView,
    DeliveryDashboardView,
    PanelView,
    StatusChangeView,
    StockDashboardView,
)
from criticals.source_views import LRRDashboardView, SQVIDashboardView

urlpatterns = [
    path("busca/", GlobalSearchView.as_view(), name="global-search"),
    path("painel/", PanelView.as_view(), name="critical-panel"),
    path("painel/estoque/", StockDashboardView.as_view(), name="critical-stock-dashboard"),
    path("painel/entregas/", DeliveryDashboardView.as_view(), name="critical-delivery-dashboard"),
    path("fontes/sqvi/", SQVIDashboardView.as_view(), name="critical-sqvi-dashboard"),
    path("fontes/lrr/", LRRDashboardView.as_view(), name="critical-lrr-dashboard"),
    path("itens/", CriticalItemListView.as_view(), name="critical-item-list"),
    path("itens/inconsistencias/", InconsistencyView.as_view(), name="critical-inconsistencies"),
    path("itens/<int:pk>/", CriticalItemDetailView.as_view(), name="critical-item-detail"),
    path("itens/<int:pk>/entregas/nova/", DeliveryCreateView.as_view(), name="delivery-create"),
    path("itens/<int:pk>/status/", StatusChangeView.as_view(), name="status-change"),
]
