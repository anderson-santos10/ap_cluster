from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from criticals.base_load import LoadRefused, apply_prepared, classify_prepared, confirm_local_database
from criticals.models import CriticalItem, Delivery, StatusChange
from criticals.preparation import BASE_SOURCE, prepare_base_row


def _prepared(**overrides):
    values = {
        "material": "MAT-1",
        "center": "C01",
        "description": "Descricao sintetica",
        "lrr": None,
        "forecast": "*",
        "status": "Pendente",
        "observation": "",
        "quantity": Decimal("-3"),
        "delivered_on": None,
    }
    values.update(overrides)
    row_number = values.pop("row_number", 4)
    return prepare_base_row(values, row_number)


class BaseLoadTests(TestCase):
    def test_isolated_database_refuses_the_operational_commands(self):
        with self.assertRaises(LoadRefused):
            confirm_local_database()
        with self.assertRaises(CommandError):
            call_command("importar_base", stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command("importar_base", "--autorizar-carga", stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command("prevalidar_base", stdout=StringIO())

    def test_confirmed_database_still_refuses_the_real_load(self):
        with patch(
            "criticals.management.commands.importar_base.confirm_local_database",
            return_value={"name": "apcluster"},
        ):
            with patch(
                "criticals.management.commands.importar_base.read_base_rows"
            ) as read_rows:
                with self.assertRaises(CommandError):
                    call_command("importar_base", stdout=StringIO())
                read_rows.assert_not_called()

    def test_preview_is_idempotent_and_reports_conflicts_without_updating(self):
        prepared = _prepared()
        first = classify_prepared([prepared], {}, {}, 0)
        self.assertEqual(first["resumo"]["novo_item"], 1)
        self.assertEqual(first["resumo"]["nova_entrega"], 1)
        self.assertEqual(first["resumo"]["atualizados"], 0)
        apply_prepared([prepared], authorized=True)
        second = apply_prepared([prepared], authorized=True)
        self.assertEqual(second["itens_criados"], 0)
        self.assertEqual(second["entregas_criadas"], 0)
        self.assertEqual(CriticalItem.objects.count(), 1)
        self.assertEqual(Delivery.objects.count(), 1)
        changed = _prepared(description="Outra descricao", quantity=Decimal("9"))
        preview = classify_prepared(
            [changed],
            {
                ("MAT-1", "C01"): {
                    "material": "MAT-1",
                    "center": "C01",
                    "description": "Descricao sintetica",
                    "lrr": None,
                    "forecast_on": None,
                    "forecast_original": "*",
                    "status": "Pendente",
                    "observation": "",
                }
            },
            {
                (BASE_SOURCE, 4): {
                    "source": BASE_SOURCE,
                    "source_row": 4,
                    "quantity": Decimal("-3.000"),
                    "delivered_on": None,
                    "author": None,
                    "material": "MAT-1",
                    "center": "C01",
                }
            },
            1,
        )
        self.assertEqual(preview["resumo"]["revisar"], 1)
        self.assertEqual(preview["resumo"]["atualizados"], 0)
        apply_prepared([changed], authorized=True)
        item = CriticalItem.objects.get()
        delivery = Delivery.objects.get()
        self.assertEqual(item.description, "Descricao sintetica")
        self.assertEqual(item.forecast_original, "*")
        self.assertIsNone(item.forecast_on)
        self.assertEqual(delivery.quantity, Decimal("-3.000"))
        self.assertIsNone(delivery.delivered_on)
        self.assertTrue(delivery.requires_review)

    def test_manual_delivery_and_status_history_stay_untouched(self):
        prepared = _prepared(quantity=None, delivered_on=None)
        apply_prepared([prepared], authorized=True)
        item = CriticalItem.objects.get()
        manual = Delivery.objects.create(item=item, quantity=Decimal("2"), delivered_on=date(2026, 6, 15))
        StatusChange.objects.create(item=item, status="Roteiro setembro")
        apply_prepared([prepared], authorized=True)
        self.assertTrue(Delivery.objects.filter(pk=manual.pk, source="").exists())
        self.assertTrue(StatusChange.objects.filter(status="Roteiro setembro").exists())
        self.assertEqual(item.status, "Pendente")

    def test_spaced_codes_are_not_merged(self):
        first = _prepared(material="MAT-1", center="C01", row_number=4, quantity=None)
        second = _prepared(material="MAT-1 ", center="C02", row_number=5, quantity=None)
        preview = classify_prepared([first, second], {}, {}, 0)
        self.assertEqual(len(preview["colisoes"]), 1)
        apply_prepared([first, second], authorized=True)
        self.assertEqual(CriticalItem.objects.count(), 2)

    def test_load_without_authorization_writes_nothing(self):
        with self.assertRaises(LoadRefused):
            apply_prepared([_prepared()], authorized=False)
        self.assertEqual(CriticalItem.objects.count(), 0)
