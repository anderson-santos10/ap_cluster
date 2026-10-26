"""Banco isolado dos testes.

A aplicação continua em config.settings.local, com o PostgreSQL local.
Este módulo usa só memória e não grava o banco apcluster.
"""

from .local import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
