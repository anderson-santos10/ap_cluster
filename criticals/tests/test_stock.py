from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from criticals.models import CriticalItem, StockPosition


class StockDetailTests(TestCase):
    def setUp(self):
        self.spaced = CriticalItem.objects.create(
            material="GP069610 ",
            center="B865",
            description="LEVEL SWITCH",
            status="Pendente",
        )
        self.plain = CriticalItem.objects.create(
            material="GP069610",
            center="B864",
            description="LEVEL SWITCH",
            status="Em rota",
        )
        self.other_center = CriticalItem.objects.create(
            material="GP004975",
            center="B825",
            description="item sem estoque neste centro",
            status="Pendente",
        )
        StockPosition.objects.create(
            item=self.plain,
            material=self.plain.material,
            center=self.plain.center,
            deposit="SAV1",
            lot="N_IMP",
            unit="PC",
            stock_description=self.plain.description,
            unrestricted=Decimal("2.000"),
            in_transit=Decimal("0"),
            in_quality=Decimal("0"),
            blocked=Decimal("0"),
        )
        self.reader = _user_with("conta-estoque", "view_criticalitem")
        self.client.force_login(self.reader)

    def test_anonymous_detail_stays_protected(self):
        self.client.logout()
        response = self.client.get(reverse("critical-item-detail", args=[self.plain.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_exact_match_shows_separate_quantities(self):
        response = self._detail(self.plain)
        self.assertContains(response, "SAV1")
        self.assertContains(response, "N_IMP")
        self.assertContains(response, ">2<")
        self.assertContains(response, "Livre")
        self.assertContains(response, "Trânsito")
        self.assertContains(response, "Qualidade")
        self.assertContains(response, "Bloqueado")
        self.assertNotContains(response, "Saldo desconhecido")

    def test_trailing_space_does_not_inherit_the_other_code(self):
        response = self._detail(self.spaced)
        self.assertContains(response, "Saldo desconhecido")
        self.assertNotContains(response, "SAV1")
        self.spaced.refresh_from_db()
        self.assertEqual(self.spaced.material, "GP069610 ")

    def test_other_center_stays_unknown(self):
        response = self._detail(self.other_center)
        self.assertContains(response, "Saldo desconhecido")
        self.assertContains(response, "diferente de zero")
        self.assertNotContains(response, "SAV1")

    def test_different_deposit_and_lot_stay_separate(self):
        StockPosition.objects.create(
            item=self.plain,
            material=self.plain.material,
            center=self.plain.center,
            deposit="SAV2",
            lot="N_NAC",
            unit="PC",
            stock_description=self.plain.description,
            unrestricted=Decimal("3"),
            in_transit=Decimal("1"),
            in_quality=Decimal("0"),
            blocked=Decimal("0"),
        )
        response = self._detail(self.plain)
        self.assertContains(response, "SAV2")
        self.assertContains(response, "N_NAC")
        self.assertNotContains(response, "posição repetida")

    def test_repeated_position_is_flagged_and_not_summed(self):
        StockPosition.objects.create(
            item=self.other_center,
            material=self.other_center.material,
            center=self.other_center.center,
            deposit="SBN1",
            lot="",
            unit="PC",
            stock_description=self.other_center.description,
            unrestricted=Decimal("1946.900"),
            in_transit=Decimal("0"),
            in_quality=Decimal("0"),
            blocked=Decimal("0"),
        )
        StockPosition.objects.create(
            item=self.other_center,
            material=self.other_center.material,
            center=self.other_center.center,
            deposit="SBN1",
            lot="",
            unit="PC",
            stock_description=self.other_center.description,
            unrestricted=Decimal("1117.900"),
            in_transit=Decimal("0"),
            in_quality=Decimal("0"),
            blocked=Decimal("0"),
        )
        response = self._detail(self.other_center)
        self.assertContains(response, "posição repetida")
        self.assertContains(response, "PC com decimal")
        self.assertContains(response, "1946.9")
        self.assertContains(response, "1117.9")
        self.assertContains(response, "em branco")
        self.assertNotContains(response, "3064")
        self.other_center.refresh_from_db()
        self.assertEqual(self.other_center.description, "item sem estoque neste centro")

    def test_present_zero_stays_zero(self):
        StockPosition.objects.create(
            item=self.spaced,
            material=self.spaced.material,
            center=self.spaced.center,
            deposit="SAV1",
            lot="N_IMP",
            unit="PC",
            stock_description=self.spaced.description,
            unrestricted=Decimal("0"),
            in_transit=Decimal("0"),
            in_quality=Decimal("0"),
            blocked=Decimal("0"),
        )
        response = self._detail(self.spaced)
        self.assertContains(response, ">0<")
        self.assertNotContains(response, "Saldo desconhecido")

    def test_user_without_permission_cannot_open_the_detail(self):
        user = get_user_model().objects.create_user("sem-estoque", password="senha-de-teste-123")
        self.client.force_login(user)
        response = self._detail(self.plain)
        self.assertEqual(response.status_code, 403)

    def test_description_divergence_does_not_replace_the_item(self):
        StockPosition.objects.create(
            item=self.spaced,
            material=self.spaced.material,
            center=self.spaced.center,
            deposit="STS1",
            lot="N_IMP",
            unit="PC",
            stock_description="OUTRO TEXTO",
            unrestricted=Decimal("1"),
            in_transit=Decimal("0"),
            in_quality=Decimal("4"),
            blocked=Decimal("0"),
        )
        response = self._detail(self.spaced)
        self.assertContains(response, "descrição divergente")
        self.assertContains(response, "OUTRO TEXTO")
        self.assertContains(response, ">4<")
        self.spaced.refresh_from_db()
        self.assertEqual(self.spaced.description, "LEVEL SWITCH")

    def _detail(self, item):
        return self.client.get(reverse("critical-item-detail", args=[item.pk]))


def _user_with(username, *codenames):
    user = get_user_model().objects.create_user(username, password="senha-de-teste-123")
    permissions = Permission.objects.filter(codename__in=codenames)
    user.user_permissions.add(*permissions)
    return user
