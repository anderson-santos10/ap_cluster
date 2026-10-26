from django.contrib.auth.views import LogoutView
from django.urls import path

from accounts.views import ClusterLoginView

urlpatterns = [
    path("entrar/", ClusterLoginView.as_view(), name="login"),
    path("sair/", LogoutView.as_view(), name="logout"),
]
