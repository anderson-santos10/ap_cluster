"""Seleciona o módulo de configuração sem gravar segredos."""

import os


def configure_settings():
    """Usa produção no Railway e preserva a configuração local nos demais casos."""
    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        return
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
        return
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.local"
