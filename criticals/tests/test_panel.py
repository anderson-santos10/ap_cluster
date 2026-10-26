from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from criticals.models import CriticalItem
from criticals.panel import apply_item_filters, parse_month, summarize


class PanelCalculationTests(TestCase):
    def setUp(self):
        self.october = CriticalItem.objects.create(
            material="MAT-A",
            center="C01",
            description="alfa",
            forecast_on=date(2026, 10, 1),
            status="Em rota",
        )
        CriticalItem.objects.create(
            material="MAT-B",
            center="C01",
            description="beta",
            forecast_on=date(2026, 11, 1),
            status="Pendente",
        )
        CriticalItem.objects.create(
            material="MAT-C",
            center="C02",
            description="literal",
            forecast_original="*",
            status="Entregue",
        )
        CriticalItem.objects.create(
            material="MAT-D",
            center="C02",
            description="parcial",
            status="Entregue parcial",
        )
        CriticalItem.objects.create(
            material="MAT-E",
            center="C02",
            description="sem status",
            forecast_on=date(2026, 10, 1),
            status="",
        )

    def test_counts_percents_and_missing_forecast_stay_out_of_the_months(self):
        with self.assertNumQueries(5):
            summary = summarize(CriticalItem.objects.all())
        self.assertEqual(summary["total"], 5)
        self.assertEqual(summary["dated"], 3)
        self.assertEqual(summary["undated"], 2)
        self.assertEqual(summary["literals"], [{"forecast_original": "*", "count": 1}])
        self.assertEqual(
            [(row["label"], row["count"], row["width"]) for row in summary["centers"]],
            [("C01", 2, "66.7"), ("C02", 3, "100.0")],
        )
        self.assertEqual(
            [(row["label"], row["count"], row["percent"]) for row in summary["statuses"]],
            [
                ("Em rota", 1, Decimal("20.0")),
                ("Pendente", 1, Decimal("20.0")),
                ("Entregue", 1, Decimal("20.0")),
                ("Entregue parcial", 1, Decimal("20.0")),
                ("ausente", 1, Decimal("20.0")),
            ],
        )
        self.assertEqual(
            [(row["label"], row["count"], row["percent"], row["percent_label"]) for row in summary["months"]],
            [
                ("OUT/2026", 2, Decimal("66.7"), "66,7%"),
                ("NOV/2026", 1, Decimal("33.3"), "33,3%"),
            ],
        )
        self.assertNotIn("*", [row["label"] for row in summary["months"]])

    def test_same_status_stays_one_bar_when_the_list_is_ordered(self):
        CriticalItem.objects.create(
            material="MAT-F",
            center="C03",
            description="outra rota",
            forecast_on=date(2026, 10, 1),
            status="Em rota",
        )
        summary = summarize(apply_item_filters({}, {}))
        em_rota = [row for row in summary["statuses"] if row["status"] == "Em rota"]
        self.assertEqual(len(em_rota), 1)
        self.assertEqual(em_rota[0]["count"], 2)
        self.assertEqual(em_rota[0]["percent"], Decimal("33.3"))
        self.assertEqual(len(summary["centers"]), 3)

    def test_forecast_percent_uses_only_dated_items_in_the_filter(self):
        summary = summarize(CriticalItem.objects.filter(center="C01", status="Em rota"))
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["dated"], 1)
        self.assertEqual(summary["undated"], 0)
        self.assertEqual(summary["literals"], [])
        self.assertEqual(summary["months"][0]["percent"], Decimal("100.0"))
        self.assertEqual(summary["statuses"][0]["percent"], Decimal("100.0"))

    def test_empty_queryset_does_not_divide_by_zero(self):
        summary = summarize(CriticalItem.objects.none())
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["dated"], 0)
        self.assertEqual(summary["undated"], 0)
        self.assertEqual(summary["months"], [])
        self.assertEqual(summary["statuses"], [])

    def test_invalid_month_text_is_ignored(self):
        self.assertIsNone(parse_month("2026-13"))
        self.assertIsNone(parse_month("*"))
        self.assertEqual(parse_month("2026-10"), (2026, 10))


class PanelViewTests(TestCase):
    def setUp(self):
        PanelCalculationTests.setUp(self)
        self.user = get_user_model().objects.create_user("conta-painel", password="senha-de-teste-123")
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_criticalitem")
        )
        self.client.force_login(self.user)

    def test_anonymous_user_is_sent_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("critical-panel"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_user_without_permission_cannot_open_the_panel(self):
        outsider = get_user_model().objects.create_user("sem-painel", password="senha-de-teste-123")
        self.client.force_login(outsider)
        response = self.client.get(reverse("critical-panel"))
        self.assertEqual(response.status_code, 403)

    def test_panel_shows_center_codes_counts_and_links(self):
        before = CriticalItem.objects.count()
        response = self.client.get(reverse("critical-panel"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CriticalItem.objects.count(), before)
        self.assertContains(response, "Itens por centro")
        self.assertContains(response, "Status da entrega")
        self.assertContains(response, "Total de críticos")
        self.assertContains(response, "Previsão no parque")
        self.assertContains(response, "C01")
        self.assertContains(response, "OUT/2026")
        self.assertContains(response, "66,7%")
        self.assertContains(response, "Sem data válida: 2")
        self.assertContains(response, "*")
        self.assertNotContains(response, "Total Geral")
        self.assertNotContains(response, "Terra Santa")
        self.assertNotContains(response, "Quant. PO")
        summary = response.context["summary"]
        self.assertEqual(summary["total"], 5)
        self.assertIn("centro=C01", summary["centers"][0]["list_url"])
        self.assertIn("status=Em+rota", summary["statuses"][0]["list_url"])
        self.assertIn("previsao=2026-10", summary["months"][0]["list_url"])
        self.assertIn("sem_previsao=1", summary["undated_url"])

    def test_combined_filter_reduces_every_chart(self):
        response = self.client.get(
            reverse("critical-panel"),
            {"centro": "C01", "status": "Em rota"},
        )
        summary = response.context["summary"]
        self.assertEqual(summary["total"], 1)
        self.assertEqual([row["label"] for row in summary["centers"]], ["C01"])
        self.assertEqual([row["label"] for row in summary["statuses"]], ["Em rota"])
        self.assertEqual([row["label"] for row in summary["months"]], ["OUT/2026"])
        self.assertEqual(summary["undated"], 0)
        self.assertIn("centro=C01", summary["total_url"])
        self.assertIn("status=Em+rota", summary["total_url"])

    def test_unknown_filter_does_not_fall_back_to_all_items(self):
        response = self.client.get(reverse("critical-panel"), {"centro": "ZZZ"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["total"], 0)
        self.assertContains(response, "não corresponde")

    def test_list_status_is_exact_and_keeps_the_forecast_slice(self):
        delivered = self.client.get(reverse("critical-item-list"), {"status": "Entregue"})
        self.assertContains(delivered, "MAT-C")
        self.assertNotContains(delivered, "MAT-D")
        october = self.client.get(reverse("critical-item-list"), {"previsao": "2026-10"})
        self.assertContains(october, "MAT-A")
        self.assertContains(october, "MAT-E")
        self.assertNotContains(october, "MAT-B")
        self.assertContains(october, "OUT/2026")
        undated = self.client.get(reverse("critical-item-list"), {"sem_previsao": "1"})
        self.assertContains(undated, "MAT-C")
        self.assertContains(undated, "MAT-D")
        self.assertNotContains(undated, "MAT-A")
        dated = self.client.get(reverse("critical-item-list"), {"com_previsao": "1"})
        self.assertContains(dated, "MAT-A")
        self.assertNotContains(dated, "MAT-C")
        absent = self.client.get(reverse("critical-item-list"), {"status_ausente": "1"})
        self.assertContains(absent, "MAT-E")
        self.assertNotContains(absent, "MAT-A")
        ignored = self.client.get(reverse("critical-item-list"), {"previsao": "*"})
        self.assertContains(ignored, "MAT-A")
        self.assertContains(ignored, "MAT-C")
