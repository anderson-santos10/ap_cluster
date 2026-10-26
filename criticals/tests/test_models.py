from datetime import date, datetime, timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from criticals.models import CriticalItem, Delivery, StatusChange


class CriticalItemTests(TestCase):
    def test_material_and_center_identify_one_item(self):
        CriticalItem.objects.create(
            material="GP124403",
            center="B856",
            description="Texto informado na linha",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CriticalItem.objects.create(
                    material="GP124403",
                    center="B856",
                    description="Outra linha da mesma chave",
                )
        CriticalItem.objects.create(
            material="GP124403",
            center="B865",
            description="Mesmo material em outro centro",
        )
        self.assertEqual(CriticalItem.objects.filter(material="GP124403").count(), 2)

    def test_numeric_material_code_stays_text(self):
        item = CriticalItem.objects.create(
            material="4060",
            center="B825",
            description="Código numérico da Base",
        )
        item.refresh_from_db()
        self.assertEqual(item.material, "4060")
        self.assertIsInstance(item.material, str)

    def test_description_is_stored_as_informed(self):
        item = CriticalItem.objects.create(
            material="GP124403",
            center="B856",
            description="Primeira descrição",
        )
        other = CriticalItem.objects.create(
            material="GP124403",
            center="B864",
            description="Segunda descrição",
        )
        self.assertEqual(item.description, "Primeira descrição")
        self.assertEqual(other.description, "Segunda descrição")

    def test_blank_lrr_stays_distinct_from_zero(self):
        blank = CriticalItem.objects.create(
            material="GP000001",
            center="B856",
            description="LRR vazio",
            lrr=None,
        )
        zero = CriticalItem.objects.create(
            material="GP000002",
            center="B856",
            description="LRR zero",
            lrr=Decimal("0"),
        )
        blank.refresh_from_db()
        zero.refresh_from_db()
        self.assertIsNone(blank.lrr)
        self.assertEqual(zero.lrr, Decimal("0.000"))
        self.assertNotEqual(blank.lrr, zero.lrr)

    def test_forecast_on_the_first_day_keeps_that_day(self):
        item = CriticalItem.objects.create(
            material="GP000003",
            center="B856",
            description="Previsão de mês",
            forecast_on=date(2026, 8, 1),
        )
        item.refresh_from_db()
        self.assertEqual(item.forecast_on, date(2026, 8, 1))
        self.assertEqual(item.forecast_original, "")

    def test_original_forecast_mark_is_not_stored_as_a_date(self):
        item = CriticalItem.objects.create(
            material="GP000006",
            center="B856",
            description="Previsão não interpretada",
            forecast_original="*",
        )
        item.refresh_from_db()
        self.assertEqual(item.forecast_original, "*")
        self.assertIsNone(item.forecast_on)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                item.forecast_on = date(2026, 8, 1)
                item.save()

    def test_legacy_status_remains_after_the_current_value_changes(self):
        user = get_user_model().objects.create_user("conta-teste")
        item = CriticalItem.objects.create(
            material="GP000004",
            center="B856",
            description="Status legado",
            status="Roteiro setembro",
        )
        recorded = StatusChange.objects.create(
            item=item,
            status="Roteiro setembro",
            changed_by=user,
            changed_at=datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc),
        )
        item.status = "Em rota"
        item.save(update_fields=["status"])
        recorded.refresh_from_db()
        self.assertEqual(item.status, "Em rota")
        self.assertEqual(recorded.status, "Roteiro setembro")
        self.assertEqual(recorded.changed_by, user)
        user.delete()
        recorded.refresh_from_db()
        self.assertIsNone(recorded.changed_by)
        self.assertTrue(StatusChange.objects.filter(pk=recorded.pk).exists())


class DeliveryTests(TestCase):
    def setUp(self):
        self.item = CriticalItem.objects.create(
            material="GP000010",
            center="B857",
            description="Item com entregas",
        )

    def test_negative_quantity_is_preserved(self):
        delivery = Delivery.objects.create(
            item=self.item,
            quantity=Decimal("-7"),
            delivered_on=date(2026, 6, 15),
        )
        delivery.refresh_from_db()
        self.assertEqual(delivery.quantity, Decimal("-7.000"))
        self.assertLess(delivery.quantity, 0)
        self.assertTrue(delivery.requires_review)
        positive = Delivery.objects.create(item=self.item, quantity=Decimal("4"))
        self.assertFalse(positive.requires_review)

    def test_item_can_have_several_deliveries(self):
        Delivery.objects.create(item=self.item, quantity=Decimal("-7"))
        Delivery.objects.create(
            item=self.item,
            quantity=Decimal("4"),
            delivered_on=date(2026, 10, 30),
        )
        self.assertEqual(self.item.deliveries.count(), 2)
        self.assertIsNone(self.item.deliveries.order_by("id").first().delivered_on)

    def test_author_is_optional_and_uses_an_existing_user(self):
        user = get_user_model().objects.create_user("conta-teste")
        without_author = Delivery.objects.create(
            item=self.item,
            quantity=Decimal("1"),
        )
        with_author = Delivery.objects.create(
            item=self.item,
            quantity=Decimal("2"),
            author=user,
        )
        self.assertIsNone(without_author.author)
        self.assertEqual(with_author.author, user)
        user.delete()
        with_author.refresh_from_db()
        self.assertIsNone(with_author.author)
        self.assertTrue(Delivery.objects.filter(pk=with_author.pk).exists())

    def test_source_row_identifies_one_imported_delivery(self):
        Delivery.objects.create(
            item=self.item,
            quantity=Decimal("-7"),
            source="criticos-ap-cluster:Base",
            source_row=12,
        )
        Delivery.objects.create(
            item=self.item,
            quantity=Decimal("-7"),
            delivered_on=date(2026, 6, 15),
            source="criticos-ap-cluster:Base",
            source_row=13,
        )
        Delivery.objects.create(
            item=self.item,
            quantity=Decimal("0"),
            source="outra-fonte",
            source_row=12,
        )
        self.assertEqual(self.item.deliveries.count(), 3)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Delivery.objects.create(
                    item=self.item,
                    quantity=Decimal("4"),
                    source="criticos-ap-cluster:Base",
                    source_row=12,
                )

    def test_manual_deliveries_do_not_use_the_import_identity(self):
        Delivery.objects.create(item=self.item, quantity=Decimal("1"))
        Delivery.objects.create(item=self.item, quantity=Decimal("2"))
        self.assertEqual(self.item.deliveries.filter(source="", source_row=None).count(), 2)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Delivery.objects.create(
                    item=self.item,
                    quantity=Decimal("3"),
                    source="criticos-ap-cluster:Base",
                )

    def test_removing_the_item_removes_its_deliveries(self):
        Delivery.objects.create(item=self.item, quantity=Decimal("1"))
        item_id = self.item.pk
        self.item.delete()
        self.assertFalse(Delivery.objects.filter(item_id=item_id).exists())
