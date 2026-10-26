import os
from pathlib import Path


def _load_local_env():
    """Lê o .env local sem substituir variáveis já definidas e sem exibi-las."""
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if not env_file.is_file():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            os.environ.setdefault(key, value.strip())


_load_local_env()

from .base import *  # noqa: E402,F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Sessão gravada no banco local do AP Cluster.
SESSION_ENGINE = "django.contrib.sessions.backends.db"
