import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from criticals.models import CriticalItem, Delivery


class GlobalSearchTests(TestCase):
    def setUp(self):
        self.spaced = CriticalItem.objects.create(
            material="MAT-1 ",
            center="C01",
            description="Bomba centrífuga",
            status="Em rota",
            observation="observação interna",
        )
        self.other = CriticalItem.objects.create(
            material="MAT-1",
            center="C02",
            description="100% algodão_especial",
            status="Entregue",
        )
        self.hidden = CriticalItem.objects.create(
            material="SEGREDO-9",
            center="C09",
            description="não deve aparecer sem permissão",
            status="Pendente",
        )
        self.delivery = Delivery.objects.create(
            item=self.spaced,
            quantity=Decimal("-4.000"),
            delivered_on=date(2026, 10, 15),
            source="origem-sintetica",
            source_row=4,
        )
        Delivery.objects.create(
            item=self.hidden,
            quantity=Decimal("9.000"),
            source="origem-oculta",
            source_row=9,
        )
        self.reader = _user_with(
            "conta-busca",
            "view_criticalitem",
            "view_delivery",
        )
        self.client.force_login(self.reader)

    def test_anonymous_request_is_rejected(self):
        self.client.logout()
        response = self.client.get(reverse("global-search"), {"q": "MAT"})
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("MAT-1", response.content.decode())

    def test_partial_code_returns_distinct_items_and_a_real_url(self):
        payload = self._search("mat-1")
        titles = [row["title"] for row in payload["groups"][0]["results"]]
        self.assertIn("MAT-1 ", titles)
        self.assertIn("MAT-1", titles)
        self.assertNotIn("SEGREDO-9", titles)
        for row in payload["groups"][0]["results"]:
            self.assertTrue(row["url"].startswith("/itens/"))
            detail = self.client.get(row["url"])
            self.assertEqual(detail.status_code, 200)

    def test_description_center_and_status_match_without_changing_rows(self):
        before = CriticalItem.objects.count()
        by_description = self._search("centrífuga")
        self.assertEqual(by_description["groups"][0]["results"][0]["title"], "MAT-1 ")
        by_center = self._search("c02")
        self.assertEqual(
            [row["title"] for row in by_center["groups"][0]["results"]],
            ["MAT-1"],
        )
        by_status = self._search("em rota")
        self.assertEqual(by_status["groups"][0]["results"][0]["meta"].endswith("Em rota"), True)
        self.assertEqual(CriticalItem.objects.count(), before)
        self.spaced.refresh_from_db()
        self.assertEqual(self.spaced.material, "MAT-1 ")

    def test_delivery_search_links_to_the_item_and_hides_other_records(self):
        payload = self._search("origem-sintetica")
        names = [group["category"] for group in payload["groups"]]
        self.assertEqual(names, ["itens", "entregas"])
        delivery = payload["groups"][1]["results"][0]
        self.assertIn("#entrega-", delivery["url"])
        self.assertIn("-4", delivery["meta"])
        self.assertNotIn("origem-oculta", response_text(payload))
        self.assertNotIn("SEGREDO-9", response_text(payload))

    def test_reader_without_delivery_permission_does_not_receive_deliveries(self):
        limited = _user_with("conta-so-item", "view_criticalitem")
        self.client.force_login(limited)
        payload = self._search("MAT-1")
        self.assertEqual([group["category"] for group in payload["groups"]], ["itens"])
        self.assertNotIn("origem-sintetica", response_text(payload))

    def test_delivery_permission_without_item_access_returns_nothing(self):
        limited = _user_with("conta-so-entrega", "view_delivery")
        self.client.force_login(limited)
        payload = self._search("SEGREDO")
        self.assertEqual(payload["groups"], [])
        self.assertNotIn("SEGREDO-9", response_text(payload))

    def test_user_without_permissions_learns_nothing_about_existing_rows(self):
        outsider = _user_with("conta-sem-busca")
        self.client.force_login(outsider)
        payload = self._search("SEGREDO")
        self.assertEqual(payload["groups"], [])
        self.assertNotIn("SEGREDO-9", response_text(payload))

    def test_empty_short_and_long_queries(self):
        empty = self._search("")
        self.assertEqual(empty["groups"], [])
        self.assertIn("2 caracteres", empty["message"])
        short = self.client.get(reverse("global-search"), {"q": " a "})
        self.assertEqual(short.status_code, 200)
        self.assertEqual(short.json()["groups"], [])
        long_text = "x" * 81
        rejected = self.client.get(reverse("global-search"), {"q": long_text})
        self.assertEqual(rejected.status_code, 400)
        self.assertNotIn("MAT-1", rejected.content.decode())

    def test_special_characters_do_not_break_the_query(self):
        lone = self._search("%")
        self.assertEqual(lone["groups"], [])
        payload = self._search("0%")
        self.assertEqual(payload["groups"][0]["results"][0]["title"], "MAT-1")
        underscore = self._search("_especial")
        self.assertEqual(underscore["groups"][0]["results"][0]["title"], "MAT-1")
        broken = self._search("<script>alert(1)</script>")
        self.assertEqual(broken["groups"][0]["results"], [])
        self.assertEqual(broken["groups"][1]["results"], [])

    def test_results_stop_at_the_category_limit(self):
        for index in range(10):
            CriticalItem.objects.create(
                material=f"LOTE-{index:02d}",
                center="C01",
                description="série de limite",
                status="Pendente",
            )
        payload = self._search("LOTE-")
        self.assertEqual(len(payload["groups"][0]["results"]), 8)

    def test_authenticated_pages_show_one_search_field(self):
        response = self.client.get(reverse("critical-item-list"))
        self.assertContains(response, "Buscar itens, centros, entregas...")
        self.assertContains(response, 'data-search-url="/busca/"')
        self.assertEqual(response.content.decode().count('class="global-search"'), 1)
        panel = self.client.get(reverse("critical-panel"))
        self.assertContains(panel, "Total de críticos")
        self.assertContains(panel, "global-search-input")

    def test_list_filter_still_excludes_partial_status(self):
        response = self.client.get(reverse("critical-item-list"), {"status": "Entregue"})
        self.assertContains(response, "MAT-1")
        self.assertNotContains(response, "MAT-1 ")
        self.assertNotContains(response, "Em rota")

    def _search(self, term):
        response = self.client.get(reverse("global-search"), {"q": term})
        self.assertEqual(response.status_code, 200)
        return response.json()


class SearchScriptTests(SimpleTestCase):
    def test_script_uses_text_nodes_and_keyboard_controls(self):
        script = Path(settings.BASE_DIR, "static", "js", "app.js").read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", script)
        self.assertNotIn("localStorage", script)
        self.assertNotIn("sessionStorage", script)
        self.assertIn("AbortController", script)
        self.assertIn("Escape", script)
        self.assertIn("ctrlKey", script)
        self.assertIn("metaKey", script)
        self.assertIn("textContent", script)

    def test_closed_panel_does_not_keep_a_result_to_open(self):
        script = Path(settings.BASE_DIR, "static", "js", "app.js").read_text(encoding="utf-8")
        submit = script.split('form.addEventListener("submit"', 1)[1].split(
            'document.addEventListener("click"', 1
        )[0]
        close = script.split("function closePanel()", 1)[1].split("function clearPanel()", 1)[0]
        self.assertIn("if (panel.hidden)", submit)
        self.assertLess(submit.index("if (panel.hidden)"), submit.index("openActive()"))
        self.assertIn("options = []", close)
        self.assertIn('panel.textContent = ""', close)


def response_text(payload):
    return json.dumps(payload, ensure_ascii=False)


def _user_with(username, *codenames):
    user = get_user_model().objects.create_user(username, password="senha-de-teste-123")
    if codenames:
        permissions = Permission.objects.filter(codename__in=codenames)
        user.user_permissions.add(*permissions)
    return user
