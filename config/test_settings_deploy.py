"""Confere a seleção de configuração sem conectar em banco nem exibir segredos."""

import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent


def _child_env(**extra):
    kept = (
        "PATH",
        "SYSTEMROOT",
        "SYSTEMDRIVE",
        "WINDIR",
        "PATHEXT",
        "TEMP",
        "TMP",
        "COMSPEC",
        "PYTHONPATH",
        "PYTHONIOENCODING",
    )
    env = {key: os.environ[key] for key in kept if key in os.environ}
    env["PYTHONIOENCODING"] = "utf-8"
    env.update(extra)
    return env


class DeploySettingsTests(SimpleTestCase):
    def test_local_remains_the_default_outside_railway(self):
        saved_module = os.environ.pop("DJANGO_SETTINGS_MODULE", None)
        saved_railway = os.environ.pop("RAILWAY_ENVIRONMENT", None)
        try:
            from config.bootstrap import configure_settings

            configure_settings()
            self.assertEqual(
                os.environ["DJANGO_SETTINGS_MODULE"],
                "config.settings.local",
            )
        finally:
            if saved_module is None:
                os.environ.pop("DJANGO_SETTINGS_MODULE", None)
            else:
                os.environ["DJANGO_SETTINGS_MODULE"] = saved_module
            if saved_railway is not None:
                os.environ["RAILWAY_ENVIRONMENT"] = saved_railway

    def test_railway_selects_production_unless_module_is_explicit(self):
        saved_module = os.environ.get("DJANGO_SETTINGS_MODULE")
        saved_railway = os.environ.get("RAILWAY_ENVIRONMENT")
        try:
            os.environ.pop("DJANGO_SETTINGS_MODULE", None)
            os.environ["RAILWAY_ENVIRONMENT"] = "production"
            from config.bootstrap import configure_settings

            configure_settings()
            self.assertEqual(
                os.environ["DJANGO_SETTINGS_MODULE"],
                "config.settings.production",
            )
            os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.testing"
            configure_settings()
            self.assertEqual(
                os.environ["DJANGO_SETTINGS_MODULE"],
                "config.settings.testing",
            )
        finally:
            if saved_module is None:
                os.environ.pop("DJANGO_SETTINGS_MODULE", None)
            else:
                os.environ["DJANGO_SETTINGS_MODULE"] = saved_module
            if saved_railway is None:
                os.environ.pop("RAILWAY_ENVIRONMENT", None)
            else:
                os.environ["RAILWAY_ENVIRONMENT"] = saved_railway

    def test_production_requires_secret_key(self):
        completed = subprocess.run(
            [sys.executable, "-c", _IMPORT_PRODUCTION],
            cwd=ROOT,
            env=_child_env(
                POSTGRES_DB="apcluster",
                POSTGRES_USER="app",
                POSTGRES_PASSWORD="deploy-check-only",
                POSTGRES_HOST="postgres.internal",
                RAILWAY_PUBLIC_DOMAIN="apcluster.up.railway.app",
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", completed.stderr + completed.stdout)
        self.assertNotIn("deploy-check-only", completed.stderr + completed.stdout)

    def test_production_uses_postgres_and_rejects_sqlite_fallback(self):
        completed = subprocess.run(
            [sys.executable, "-c", _IMPORT_PRODUCTION],
            cwd=ROOT,
            env=_child_env(
                DJANGO_SECRET_KEY="deploy-check-only",
                POSTGRES_DB="apcluster",
                POSTGRES_USER="app",
                POSTGRES_PASSWORD="deploy-check-only",
                POSTGRES_HOST="postgres.internal",
                POSTGRES_PORT="5432",
                RAILWAY_PUBLIC_DOMAIN="apcluster.up.railway.app",
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("ENGINE django.db.backends.postgresql", completed.stdout)
        self.assertIn("SQLITE False", completed.stdout)
        self.assertIn("DEBUG False", completed.stdout)
        self.assertIn("NAME apcluster", completed.stdout)
        self.assertIn("HOST postgres.internal", completed.stdout)
        self.assertIn("PASSWORD_SET True", completed.stdout)
        self.assertNotIn("sqlite", completed.stdout)

    def test_production_names_missing_database_variables(self):
        completed = subprocess.run(
            [sys.executable, "-c", _IMPORT_PRODUCTION],
            cwd=ROOT,
            env=_child_env(DJANGO_SECRET_KEY="deploy-check-only"),
            capture_output=True,
            text=True,
            check=False,
        )
        message = completed.stderr + completed.stdout
        self.assertNotEqual(completed.returncode, 0)
        for name in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST"):
            self.assertIn(name, message)


_IMPORT_PRODUCTION = r"""
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.production"
try:
    from django.conf import settings
    database = settings.DATABASES["default"]
    engine = database["ENGINE"]
    print("ENGINE", engine)
    print("SQLITE", "sqlite" in engine)
    print("DEBUG", settings.DEBUG)
    print("NAME", database["NAME"])
    print("HOST", database["HOST"])
    print("PASSWORD_SET", bool(database["PASSWORD"]))
    print("ALLOWED", ",".join(settings.ALLOWED_HOSTS))
except Exception as exc:
    print(type(exc).__name__)
    print(exc)
    raise
"""
