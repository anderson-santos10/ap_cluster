from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView


class ClusterLoginView(LoginView):
    template_name = "registration/login.html"


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/home.html"
