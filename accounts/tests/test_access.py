import os

from django.conf import settings
from django.test import Client, SimpleTestCase, override_settings
from django.urls import NoReverseMatch, reverse

import config.settings.local as local_settings


@override_settings(SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies")
class AccessTests(SimpleTestCase):
    def test_login_page_is_available(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entrar")
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertNotContains(response, "cadastr", html=False)

    def test_home_requires_authentication(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_admin_index_requires_authentication(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_logout_rejects_get(self):
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)

    def test_logout_post_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("login"))
        response = client.post(reverse("logout"))
        self.assertEqual(response.status_code, 403)

    def test_logout_post_with_csrf_redirects_to_login(self):
        client = Client(enforce_csrf_checks=True)
        page = client.get(reverse("login"))
        response = client.post(
            reverse("logout"),
            {"csrfmiddlewaretoken": page.context["csrf_token"]},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_there_is_no_public_registration(self):
        with self.assertRaises(NoReverseMatch):
            reverse("signup")
        response = self.client.get("/contas/cadastrar/")
        self.assertEqual(response.status_code, 404)

    def test_user_model_is_the_django_default(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "auth.User")
        self.assertTrue(local_settings.DEBUG)
        self.assertEqual(local_settings.ALLOWED_HOSTS, ["localhost", "127.0.0.1"])

    def test_only_expected_apps_were_added(self):
        custom_apps = [
            name
            for name in settings.INSTALLED_APPS
            if not name.startswith("django.")
        ]
        self.assertEqual(custom_apps, ["accounts", "criticals"])

    def test_database_is_postgresql_from_environment(self):
        database = settings.DATABASES["default"]
        self.assertEqual(database["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(database["NAME"], "apcluster")
        self.assertEqual(database["USER"], "apcluster_app")
        self.assertTrue(
            database["PASSWORD"] == os.environ.get("POSTGRES_PASSWORD", "")
        )
        self.assertIn(database["HOST"], ("localhost", "127.0.0.1"))
