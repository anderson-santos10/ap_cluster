from django.contrib import admin
from django.urls import include, path

from accounts.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("contas/", include("accounts.urls")),
    path("", include("criticals.urls")),
    path("admin/", admin.site.urls),
]
