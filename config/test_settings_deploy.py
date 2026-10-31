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
    def test_railway_start_command_binds_the_wsgi_app_to_the_platform_port(self):
        railway = (ROOT / "railway.toml").read_text(encoding="utf-8")
        entrypoint = (ROOT / "entrypoint.prod.sh").read_text(encoding="utf-8")
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn('startCommand = "/app/entrypoint.prod.sh"', railway)
        self.assertNotIn("gunicorn config.wsgi", railway)
        self.assertNotIn("qcluster", railway)
        self.assertNotIn("qcluster", entrypoint)
        self.assertNotIn("core.wsgi", entrypoint)
        self.assertNotIn(" &", entrypoint)
        self.assertIn('CMD ["/app/entrypoint.prod.sh"]', dockerfile)
        self.assertIn("config.wsgi:application", entrypoint)
        self.assertIn('0.0.0.0:${PORT:-8080}', entrypoint)
        self.assertIn("python manage.py migrate --noinput", entrypoint)
        self.assertIn("python manage.py collectstatic --noinput", entrypoint)
        self.assertIn("exec gunicorn", entrypoint)

    def test_production_whitenoise_serves_collected_static_files(self):
        completed = subprocess.run(
            [sys.executable, "-c", _SERVE_STATIC],
            cwd=ROOT,
            env=_child_env(
                DJANGO_SETTINGS_MODULE="config.settings.production",
                DJANGO_SECRET_KEY="deploy-check-only-static-files-not-a-production-secret",
                POSTGRES_DB="apcluster",
                POSTGRES_USER="app",
                POSTGRES_PASSWORD="deploy-check-only",
                POSTGRES_HOST="127.0.0.1",
                POSTGRES_PORT="5432",
                RAILWAY_PUBLIC_DOMAIN="apcluster.up.railway.app",
                DJANGO_ALLOWED_HOSTS="testserver",
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        output = completed.stdout + completed.stderr
        self.assertNotIn("deploy-check-only", output)
        self.assertEqual(completed.returncode, 0, output)
        self.assertIn("CSS 200", output)
        self.assertIn("JS 200", output)
        self.assertIn("ADMIN_CSS 200", output)
        self.assertIn("FONT 200", output)
        self.assertIn("MISSING 404", output)

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

_SERVE_STATIC = r"""
import re
from urllib.parse import urljoin

import django

django.setup()

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command
from django.template import Context, Template
from django.test import Client

security = "django.middleware.security.SecurityMiddleware"
whitenoise = "whitenoise.middleware.WhiteNoiseMiddleware"
if settings.MIDDLEWARE.index(whitenoise) != settings.MIDDLEWARE.index(security) + 1:
    raise SystemExit("middleware " + ",".join(settings.MIDDLEWARE))
if settings.STORAGES["default"]["BACKEND"] != "django.core.files.storage.FileSystemStorage":
    raise SystemExit("default storage " + settings.STORAGES["default"]["BACKEND"])
expected_static = "whitenoise.storage.CompressedManifestStaticFilesStorage"
if settings.STORAGES["staticfiles"]["BACKEND"] != expected_static:
    raise SystemExit("static storage " + settings.STORAGES["staticfiles"]["BACKEND"])
if settings.STATIC_URL != "/static/":
    raise SystemExit("STATIC_URL " + settings.STATIC_URL)

call_command("collectstatic", interactive=False, verbosity=1)

template = Template("{% load static %}{% static 'css/app.css' %} {% static 'js/app.js' %}")
css_url, js_url = template.render(Context()).split()
print("CSS_URL", css_url)
print("JS_URL", js_url)
if staticfiles_storage.url("css/app.css") != css_url:
    raise SystemExit("template url diverges from storage")

def body(response):
    return b"".join(response.streaming_content)

client = Client()
css = client.get(css_url)
js = client.get(js_url)
css_body = body(css)
js_body = body(js)
print("CSS", css.status_code, css.get("Content-Type", ""))
print("JS", js.status_code, js.get("Content-Type", ""))
if css.status_code != 200 or b"color-scheme" not in css_body:
    raise SystemExit("css body was not served")
if js.status_code != 200 or b"global-search" not in js_body:
    raise SystemExit("js body was not served")
if "text/css" not in css.get("Content-Type", ""):
    raise SystemExit("css content type")
missing = client.get("/static/css/does-not-exist.css")
print("MISSING", missing.status_code)
if missing.status_code != 404:
    raise SystemExit("missing file was not rejected")

admin_url = staticfiles_storage.url("admin/css/widgets.css")
admin = client.get(admin_url)
admin_body = body(admin)
print("ADMIN_CSS", admin.status_code)
if admin.status_code != 200 or not admin_body:
    raise SystemExit("admin css was not served")
text = admin_body.decode("utf-8")
served_font = False
for match in re.findall(r"url\(([^)]+)\)", text):
    target = match.strip().strip("\"'").split("?")[0].split("#")[0]
    if not target or target.startswith(("data:", "http://", "https://")):
        continue
    location = urljoin(admin_url, target)
    response = client.get(location)
    payload = body(response)
    print("FONT", response.status_code, location)
    if response.status_code != 200 or not payload:
        raise SystemExit("broken manifest reference " + location)
    served_font = True
    break
if not served_font:
    raise SystemExit("admin css has no rewritten static reference")
"""
