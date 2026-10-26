from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from criticals.models import CriticalItem, Delivery, StatusChange


class CriticalViewTests(TestCase):
    def setUp(self):
        self.item = CriticalItem.objects.create(
            material="MAT-1 ",
            center="C01",
            description="Descricao sintetica",
            forecast_original="*",
            status="Pendente",
        )
        CriticalItem.objects.create(
            material="MAT-1",
            center="C02",
            description="Outro centro",
            lrr=Decimal("0"),
        )

    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get(reverse("critical-item-list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_user_without_permission_cannot_open_the_list_by_url(self):
        user = get_user_model().objects.create_user("sem-perfil", password="senha-de-teste-123")
        self.client.force_login(user)
        response = self.client.get(reverse("critical-item-list"))
        self.assertEqual(response.status_code, 403)

    def test_reader_can_filter_and_see_literal_forecast_and_spacing(self):
        user = _user_with("conta-leitura", "view_criticalitem")
        self.client.force_login(user)
        response = self.client.get(reverse("critical-item-list"), {"material": "MAT-1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MAT-1 ")
        self.assertContains(response, "não foram unidos")
        detail = self.client.get(reverse("critical-item-detail", args=[self.item.pk]))
        self.assertContains(detail, "*")
        self.assertContains(detail, "Valor literal preservado")
        self.assertContains(detail, "Saldo desconhecido")
        self.assertNotContains(detail, "Registrar entrega")
        self.assertNotContains(detail, "Alterar status")
        report = self.client.get(reverse("critical-inconsistencies"))
        self.assertContains(report, "espaço preservado")
        self.assertContains(report, "MAT-1")

    def test_stock_profile_can_register_a_negative_delivery_and_cannot_change_status(self):
        user = _user_with("conta-estoque", "view_criticalitem", "add_delivery")
        self.client.force_login(user)
        denied = self.client.get(reverse("status-change", args=[self.item.pk]))
        self.assertEqual(denied.status_code, 403)
        response = self.client.post(
            reverse("delivery-create", args=[self.item.pk]),
            {"quantity": "-4", "delivered_on": ""},
        )
        self.assertRedirects(response, reverse("critical-item-detail", args=[self.item.pk]))
        delivery = Delivery.objects.get()
        self.assertEqual(delivery.quantity, Decimal("-4.000"))
        self.assertIsNone(delivery.delivered_on)
        self.assertEqual(delivery.source, "")
        self.assertTrue(delivery.requires_review)
        self.assertEqual(delivery.author, user)

    def test_status_change_keeps_the_previous_value(self):
        user = _user_with("conta-status", "view_criticalitem", "change_critical_status")
        self.client.force_login(user)
        response = self.client.post(
            reverse("status-change", args=[self.item.pk]),
            {"status": "Em rota"},
        )
        self.assertRedirects(response, reverse("critical-item-detail", args=[self.item.pk]))
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "Em rota")
        recorded = StatusChange.objects.get()
        self.assertEqual(recorded.status, "Pendente")
        self.assertEqual(recorded.changed_by, user)
        self.client.post(
            reverse("status-change", args=[self.item.pk]),
            {"status": "Entregue"},
        )
        self.assertTrue(StatusChange.objects.filter(status="Pendente").exists())
        self.assertTrue(StatusChange.objects.filter(status="Em rota").exists())

    def test_purchasing_profile_cannot_register_a_delivery(self):
        user = _user_with("conta-compras", "view_criticalitem")
        self.client.force_login(user)
        response = self.client.post(
            reverse("delivery-create", args=[self.item.pk]),
            {"quantity": "1", "delivered_on": ""},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Delivery.objects.count(), 0)


def _user_with(username, *codenames):
    user = get_user_model().objects.create_user(username, password="senha-de-teste-123")
    permissions = Permission.objects.filter(codename__in=codenames)
    user.user_permissions.add(*permissions)
    return user
