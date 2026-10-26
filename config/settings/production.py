"""Produção no Railway.

Não lê arquivo .env, não cria chave secreta e não usa SQLite.
O banco continua o PostgreSQL configurado por POSTGRES_DB, POSTGRES_USER,
POSTGRES_PASSWORD, POSTGRES_HOST e POSTGRES_PORT.
"""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: E402,F403

DEBUG = False


def _hosts_from_env():
    hosts = [
        item.strip()
        for item in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
        if item.strip()
    ]
    for name in ("RAILWAY_PUBLIC_DOMAIN", "RAILWAY_PRIVATE_DOMAIN"):
        domain = os.environ.get(name, "").strip()
        if domain and domain not in hosts:
            hosts.append(domain)
    if not hosts:
        hosts.append(".up.railway.app")
    return hosts


ALLOWED_HOSTS = _hosts_from_env()

CSRF_TRUSTED_ORIGINS = ["https://*.up.railway.app"]
for host in ALLOWED_HOSTS:
    if host.startswith("."):
        continue
    origin = f"https://{host}"
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

_REQUIRED_DATABASE = (
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
)
_missing_database = [
    name for name in _REQUIRED_DATABASE if not os.environ.get(name, "").strip()
]
if _missing_database:
    raise ImproperlyConfigured(
        "A produção usa PostgreSQL pelas variáveis POSTGRES_*. "
        "Defina: " + ", ".join(_missing_database) + "."
    )

if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":  # noqa: F405
    raise ImproperlyConfigured("A configuração de produção deve usar PostgreSQL.")

STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
