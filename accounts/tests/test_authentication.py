from io import StringIO
import secrets
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from accounts.profiles import PROFILES


def _password():
    return secrets.token_urlsafe(18)


class AuthenticationReadyTests(SimpleTestCase):
    def test_credential_suite_waits_for_an_isolated_database(self):
        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            self.skipTest("Coberto pelos testes de credencial deste módulo.")
        self.skipTest(
            "As credenciais são exercitadas com config.settings.testing, "
            "sem usar o PostgreSQL do projeto."
        )


if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":

    class AuthenticationTests(TestCase):
        def test_active_superuser_uses_the_same_login_screen(self):
            password = _password()
            user = get_user_model().objects.create_superuser(
                "superusuario-teste",
                "",
                password,
            )
            self.assertEqual(user.groups.count(), 0)
            response = self.client.post(
                reverse("login"),
                {"username": "superusuario-teste", "password": password},
            )
            self.assertRedirects(response, reverse("home"))
            self.assertContains(self.client.get(reverse("home")), "superusuario-teste")

        def test_valid_login_opens_home_and_logout_closes_it(self):
            password = _password()
            user_model = get_user_model()
            user_model.objects.create_user("conta-teste", password=password)

            response = self.client.post(
                reverse("login"),
                {"username": "conta-teste", "password": password},
            )
            self.assertRedirects(response, reverse("home"))
            home = self.client.get(reverse("home"))
            self.assertContains(home, "conta-teste")
            self.assertContains(home, 'method="post"')
            self.assertContains(home, "csrfmiddlewaretoken")

            logged_out = self.client.post(reverse("logout"))
            self.assertRedirects(logged_out, reverse("login"))
            blocked = self.client.get(reverse("home"))
            self.assertEqual(blocked.status_code, 302)
            self.assertIn(reverse("login"), blocked["Location"])

        def test_invalid_login_is_rejected(self):
            password = _password()
            get_user_model().objects.create_user("conta-teste", password=password)
            response = self.client.post(
                reverse("login"),
                {"username": "conta-teste", "password": _password()},
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Entrar")
            self.assertFalse(response.wsgi_request.user.is_authenticated)

        def test_login_without_csrf_is_rejected(self):
            client = Client(enforce_csrf_checks=True)
            client.get(reverse("login"))
            response = client.post(reverse("login"), {})
            self.assertEqual(response.status_code, 403)

        def test_login_with_csrf_and_unknown_user_stays_on_the_form(self):
            client = Client(enforce_csrf_checks=True)
            page = client.get(reverse("login"))
            response = client.post(
                reverse("login"),
                {
                    "username": "conta-inexistente",
                    "password": _password(),
                    "csrfmiddlewaretoken": page.context["csrf_token"],
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Entrar")

        def test_external_next_is_not_followed(self):
            password = _password()
            get_user_model().objects.create_user("conta-teste", password=password)
            response = self.client.post(
                reverse("login"),
                {
                    "username": "conta-teste",
                    "password": password,
                    "next": "https://example.com",
                },
            )
            self.assertRedirects(response, reverse("home"))

        def test_profiles_receive_only_the_confirmed_permissions(self):
            expected = {
                "Compras": {
                    "view_criticalitem",
                    "view_delivery",
                    "view_statuschange",
                },
                "Estoque/Operação": {
                    "view_criticalitem",
                    "view_delivery",
                    "view_statuschange",
                    "add_delivery",
                },
                "Administração": {
                    "view_criticalitem",
                    "view_delivery",
                    "view_statuschange",
                    "view_user",
                    "add_user",
                    "change_user",
                },
            }
            blocked = {
                "change_criticalitem",
                "change_critical_status",
                "add_statuschange",
                "change_delivery",
                "delete_delivery",
                "delete_user",
                "change_group",
            }
            for name, codenames in expected.items():
                group = Group.objects.get(name=name)
                present = set(group.permissions.values_list("codename", flat=True))
                self.assertEqual(present, codenames)
                self.assertTrue(blocked.isdisjoint(present))

        def test_business_profiles_do_not_receive_operational_access(self):
            purchasing = Group.objects.get(name="Compras")
            stock = Group.objects.get(name="Estoque/Operação")
            buyer = get_user_model().objects.create_user("conta-compras")
            operator = get_user_model().objects.create_user("conta-estoque")
            buyer.groups.add(purchasing)
            operator.groups.add(stock)
            self.assertTrue(buyer.has_perm("criticals.view_criticalitem"))
            self.assertFalse(buyer.has_perm("criticals.change_criticalitem"))
            self.assertFalse(buyer.has_perm("criticals.add_delivery"))
            self.assertFalse(buyer.has_perm("criticals.change_critical_status"))
            self.assertTrue(operator.has_perm("criticals.add_delivery"))
            self.assertFalse(operator.has_perm("criticals.change_critical_status"))
            self.assertFalse(operator.has_perm("criticals.add_statuschange"))
            admin = get_user_model().objects.create_superuser(
                "superusuario-teste",
                "",
                _password(),
            )
            self.assertEqual(admin.groups.count(), 0)
            self.assertTrue(admin.has_perm("criticals.change_criticalitem"))

        def test_account_command_creates_a_regular_user(self):
            password = _password()
            with patch(
                "accounts.management.commands.criar_conta.getpass.getpass",
                side_effect=[password, password],
            ):
                call_command(
                    "criar_conta",
                    usuario="conta-teste",
                    perfil="Compras",
                    stdout=StringIO(),
                )

            user = get_user_model().objects.get(username="conta-teste")
            self.assertFalse(user.is_superuser)
            self.assertFalse(user.is_staff)
            self.assertTrue(user.is_active)
            self.assertEqual(user.email, "")
            self.assertTrue(user.groups.filter(name="Compras").exists())
            self.assertFalse(user.has_perm("auth.add_user"))
            self.assertTrue(user.check_password(password))
            self.assertTrue(
                self.client.login(username="conta-teste", password=password)
            )

        def test_account_command_rejects_mismatched_or_duplicate_users(self):
            with patch(
                "accounts.management.commands.criar_conta.getpass.getpass",
                side_effect=[_password(), _password()],
            ):
                with self.assertRaises(CommandError):
                    call_command(
                        "criar_conta",
                        usuario="conta-teste",
                        perfil="Estoque/Operação",
                        stdout=StringIO(),
                    )
            self.assertFalse(
                get_user_model().objects.filter(username="conta-teste").exists()
            )

            password = _password()
            with patch(
                "accounts.management.commands.criar_conta.getpass.getpass",
                side_effect=[password, password],
            ):
                call_command(
                    "criar_conta",
                    usuario="conta-teste",
                    perfil="Administração",
                    stdout=StringIO(),
                )
            with patch(
                "accounts.management.commands.criar_conta.getpass.getpass",
                side_effect=[password, password],
            ):
                with self.assertRaises(CommandError):
                    call_command(
                        "criar_conta",
                        usuario="conta-teste",
                        perfil="Administração",
                        stdout=StringIO(),
                    )
            self.assertEqual(
                get_user_model().objects.filter(username="conta-teste").count(),
                1,
            )
