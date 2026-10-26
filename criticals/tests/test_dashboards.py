from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from criticals.dashboards import attention, delivery_report, stock_report
from criticals.models import CriticalItem, Delivery, StockPosition


class DashboardCalculationTests(TestCase):
    def setUp(self):
        self.spaced = CriticalItem.objects.create(
            material="GP069610 ",
            center="B865",
            description="LEVEL SWITCH",
            forecast_original="*",
            status="Pendente",
        )
        self.plain = CriticalItem.objects.create(
            material="GP069610",
            center="B864",
            description="LEVEL SWITCH",
            forecast_on=date(2026, 10, 1),
            status="Em rota",
        )
        self.blank = CriticalItem.objects.create(
            material="MAT-D",
            center="C02",
            description="sem status",
            status="",
        )
        Delivery.objects.create(
            item=self.plain,
            quantity=Decimal("-2"),
            delivered_on=None,
        )
        Delivery.objects.create(
            item=self.plain,
            quantity=Decimal("4"),
            delivered_on=date(2026, 10, 15),
        )
        Delivery.objects.create(
            item=self.blank,
            quantity=Decimal("1"),
            delivered_on=date(2026, 11, 2),
        )
        StockPosition.objects.create(
            item=self.plain,
            material=self.plain.material,
            center=self.plain.center,
            deposit="SBN1",
            lot="",
            unit="PC",
            stock_description=self.plain.description,
            unrestricted=Decimal("1946.900"),
            in_transit=Decimal("0"),
            in_quality=Decimal("0"),
            blocked=Decimal("0"),
        )
        StockPosition.objects.create(
            item=self.plain,
            material=self.plain.material,
            center=self.plain.center,
            deposit="SBN1",
            lot="",
            unit="PC",
            stock_description="OUTRO TEXTO",
            unrestricted=Decimal("1117.900"),
            in_transit=Decimal("1"),
            in_quality=Decimal("0"),
            blocked=Decimal("0"),
        )

    def test_attention_uses_only_defined_review_cases(self):
        report = attention(CriticalItem.objects.all())
        self.assertEqual(report["negative"], 1)
        self.assertEqual(report["missing_dates"], 1)
        self.assertEqual(report["literals"], 1)
        self.assertEqual(report["absent_status"], 1)
        reasons = [row["reason"] for row in report["rows"]]
        self.assertNotIn("atraso", " ".join(reasons).lower())
        self.assertEqual(reasons.count("Quantidade negativa"), 1)

    def test_stock_keeps_positions_separate_and_unknown_distinct_from_zero(self):
        report = stock_report(CriticalItem.objects.all())
        self.assertEqual(report["item_count"], 3)
        self.assertEqual(report["with_position"], 1)
        self.assertEqual(report["unknown"], 2)
        self.assertEqual(report["position_count"], 2)
        self.assertEqual(report["repeated_groups"], 1)
        self.assertEqual(report["divergences"], 1)
        self.assertEqual(report["decimal_pc"], 2)
        quantities = [row["unrestricted"] for row in report["rows"]]
        self.assertEqual(quantities, ["1946.9", "1117.9"])
        self.assertNotIn("3064", quantities)
        self.assertTrue(all(row["material"] == "GP069610" for row in report["rows"]))
        self.assertNotIn("total", report)

    def test_same_deposit_on_another_item_is_not_a_repeated_group(self):
        StockPosition.objects.create(
            item=self.spaced,
            material=self.spaced.material,
            center=self.spaced.center,
            deposit="SBN1",
            lot="",
            unit="PC",
            stock_description=self.spaced.description,
            unrestricted=Decimal("5"),
            in_transit=Decimal("0"),
            in_quality=Decimal("0"),
            blocked=Decimal("0"),
        )
        report = stock_report(CriticalItem.objects.all())
        self.assertEqual(report["repeated_groups"], 1)
        self.assertEqual(report["with_position"], 2)
        self.assertEqual(report["unknown"], 1)

    def test_deliveries_keep_negative_quantity_and_leave_blank_dates_out_of_the_line(self):
        report = delivery_report(CriticalItem.objects.all(), None)
        self.assertEqual(report["total"], 3)
        self.assertEqual(report["dated"], 2)
        self.assertEqual(report["undated"], 1)
        self.assertEqual(report["negative"], 1)
        self.assertEqual([row["label"] for row in report["months"]], ["OUT/2026", "NOV/2026"])
        self.assertIn(",", report["line"])
        october = delivery_report(CriticalItem.objects.all(), "2026-10")
        self.assertEqual(october["scoped_total"], 1)
        self.assertEqual(october["rows"][0]["quantity"], "4")
        self.assertEqual(delivery_report(CriticalItem.objects.all(), "*")["scoped_total"], 3)

    def test_empty_sets_do_not_invent_quantities(self):
        stock = stock_report(CriticalItem.objects.none())
        delivery = delivery_report(CriticalItem.objects.none(), None)
        review = attention(CriticalItem.objects.none())
        self.assertEqual(stock["unknown"], 0)
        self.assertEqual(stock["unknown_items"], [])
        self.assertEqual(stock["rows"], [])
        self.assertEqual(delivery["months"], [])
        self.assertEqual(delivery["line"], "")
        self.assertEqual(review["rows"], [])


class DashboardViewTests(TestCase):
    def setUp(self):
        DashboardCalculationTests.setUp(self)
        self.user = get_user_model().objects.create_user("conta-dashboard", password="senha-de-teste-123")
        self.user.user_permissions.add(Permission.objects.get(codename="view_criticalitem"))
        self.client.force_login(self.user)

    def test_anonymous_user_is_sent_to_login(self):
        self.client.logout()
        for name in ("critical-panel", "critical-stock-dashboard", "critical-delivery-dashboard"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("login"), response["Location"])

    def test_user_without_permission_cannot_open_the_dashboards(self):
        outsider = get_user_model().objects.create_user("sem-dashboard", password="senha-de-teste-123")
        self.client.force_login(outsider)
        for name in ("critical-panel", "critical-stock-dashboard", "critical-delivery-dashboard"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403)

    def test_stock_page_shows_separate_quantities_and_unknown_stock(self):
        response = self.client.get(reverse("critical-stock-dashboard"))
        self.assertContains(response, "Saldo desconhecido")
        self.assertContains(response, "1946.9")
        self.assertContains(response, "1117.9")
        self.assertContains(response, "posição repetida")
        self.assertContains(response, "descrição divergente")
        self.assertContains(response, "PC com decimal")
        self.assertNotContains(response, "3064")
        self.assertContains(response, "GP069610 ")
        self.assertEqual(response.context["report"]["unknown"], 2)

    def test_stock_page_without_positions_does_not_show_zero_balance(self):
        StockPosition.objects.all().delete()
        response = self.client.get(reverse("critical-stock-dashboard"))
        self.assertContains(response, "diferente de zero")
        self.assertNotContains(response, "1946.9")
        self.assertEqual(response.context["report"]["unknown"], 3)
        self.assertEqual(response.context["report"]["position_count"], 0)

    def test_delivery_page_links_to_the_record_and_filters_by_month(self):
        response = self.client.get(reverse("critical-delivery-dashboard"))
        self.assertContains(response, "OUT/2026")
        self.assertContains(response, "NOV/2026")
        self.assertContains(response, "-2")
        self.assertContains(response, "entrega-")
        month = self.client.get(reverse("critical-delivery-dashboard"), {"entrega": "2026-11"})
        self.assertContains(month, "MAT-D")
        self.assertNotContains(month, "GP069610")
        self.assertEqual(month.context["report"]["scoped_total"], 1)

    def test_unknown_center_does_not_fall_back_to_all_records(self):
        response = self.client.get(reverse("critical-stock-dashboard"), {"centro": "ZZZ"})
        self.assertContains(response, "não corresponde")
        self.assertEqual(response.context["report"]["item_count"], 0)
