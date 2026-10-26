from datetime import date, datetime
from decimal import Decimal

from django.test import SimpleTestCase

from criticals.preparation import (
    BASE_SOURCE,
    PreparationError,
    REIMPORT_POLICY,
    UNKNOWN_STOCK,
    classify_position_group,
    critical_key,
    delivery_origin,
    descriptions_for_review,
    excel_serial_calendar,
    missing_stock,
    movement_key,
    normalized_code,
    normalized_collisions,
    plan_reimport,
    po_cache_relation,
    prepare_base_row,
    read_center,
    read_delivery,
    read_forecast,
    read_lrr,
    read_material,
    referenced_base_row,
    repeated_origins,
)


class PreparationTests(SimpleTestCase):
    def test_numeric_and_text_materials_stay_text(self):
        self.assertEqual(read_material(4060), "4060")
        self.assertEqual(read_material("004060"), "004060")
        preserved = prepare_base_row(_row(material="004060", quantity=None), 6)
        self.assertEqual(preserved["material"], "004060")
        self.assertIn(
            "zero_a_esquerda_preservado",
            {note["motivo"] for note in preserved["revisoes"]},
        )
        self.assertEqual(read_material("MAT-1 "), "MAT-1 ")
        self.assertEqual(critical_key("MAT-1", "C01"), ("MAT-1", "C01"))
        self.assertEqual(read_center("C01 "), "C01 ")

    def test_blank_material_or_center_is_invalid(self):
        with self.assertRaises(PreparationError):
            read_material(None)
        with self.assertRaises(PreparationError):
            read_material("   ")
        with self.assertRaises(PreparationError):
            prepare_base_row(_row(material=""), 2)
        with self.assertRaises(PreparationError):
            prepare_base_row(_row(center=""), 2)
        with self.assertRaises(PreparationError):
            prepare_base_row(_row(material="M" * 41), 2)
        with self.assertRaises(PreparationError):
            prepare_base_row(_row(center="C" * 11), 2)

    def test_empty_lrr_is_distinct_from_zero(self):
        self.assertIsNone(read_lrr(None))
        self.assertIsNone(read_lrr(""))
        self.assertEqual(read_lrr(0), Decimal("0"))
        self.assertEqual(read_lrr("2"), Decimal("2"))

    def test_forecast_keeps_month_start_and_original_token(self):
        forecast_on, original = read_forecast(datetime(2026, 8, 1, 0, 0))
        self.assertEqual(forecast_on, date(2026, 8, 1))
        self.assertEqual(original, "")
        forecast_on, original = read_forecast("*")
        self.assertIsNone(forecast_on)
        self.assertEqual(original, "*")
        forecast_on, original = read_forecast(2958465)
        self.assertIsNone(forecast_on)
        self.assertEqual(original, "2958465")

    def test_negative_quantity_is_kept_and_missing_date_stays_empty(self):
        delivery = read_delivery(-7, None)
        self.assertEqual(delivery["quantity"], Decimal("-7"))
        self.assertIsNone(delivery["delivered_on"])
        self.assertTrue(delivery["requires_review"])
        self.assertFalse(read_delivery(4, date(2026, 6, 15))["requires_review"])

    def test_blank_quantity_does_not_invent_a_delivery(self):
        self.assertIsNone(read_delivery(None, None))
        self.assertIsNone(read_delivery("", ""))
        with self.assertRaises(PreparationError):
            read_delivery(None, date(2026, 6, 15))
        with self.assertRaises(PreparationError):
            read_delivery(2, 2958465)

    def test_identical_copies_and_conflicts_do_not_resolve_a_balance(self):
        identical = classify_position_group(
            [
                {"deposito": "D1", "lote": "L1", "utilizacao_livre": 2},
                {"deposito": "D1", "lote": "L1", "utilizacao_livre": 2},
            ]
        )
        conflict = classify_position_group(
            [
                {"deposito": "D1", "lote": "L1", "utilizacao_livre": "1.5"},
                {"deposito": "D1", "lote": "L1", "utilizacao_livre": "4.5"},
            ]
        )
        self.assertEqual(identical["situacao"], "copia_identica")
        self.assertEqual(identical["efeito_se_somar"]["utilizacao_livre"], Decimal("4"))
        self.assertIsNone(identical["saldo_resolvido"])
        self.assertEqual(conflict["situacao"], "conflito")
        self.assertEqual(conflict["campos_divergentes"], ["utilizacao_livre"])
        self.assertEqual(conflict["efeito_se_somar"]["utilizacao_livre"], Decimal("6.0"))
        self.assertIsNone(conflict["saldo_resolvido"])

    def test_movement_key_is_not_the_critical_item_key(self):
        item = critical_key("MAT-1", "C01")
        first = movement_key("4500000001", 10)
        second = movement_key("4500000002", 10)
        self.assertNotEqual(item, first)
        self.assertNotEqual(first, second)
        self.assertEqual(first, ("4500000001", "10"))

    def test_description_conflict_keeps_every_text(self):
        texts = descriptions_for_review("Texto da linha", ["Texto do extrato"])
        self.assertEqual(texts, ("Texto da linha", "Texto do extrato"))
        self.assertEqual(descriptions_for_review("Igual", ["Igual"]), ())

    def test_missing_stock_is_unknown(self):
        self.assertEqual(missing_stock(), UNKNOWN_STOCK)
        self.assertNotEqual(missing_stock(), 0)

    def test_po_cache_can_follow_the_referenced_row(self):
        formula = "=SUMIF(SQVI!B:B,Base!A35,SQVI!V:V)"
        self.assertEqual(referenced_base_row(formula), 35)
        self.assertNotEqual(referenced_base_row(formula), 2)
        self.assertEqual(po_cache_relation(750, 0, 750), "segue_referencia")
        self.assertEqual(po_cache_relation(0, 0, 0), "empate")
        self.assertEqual(po_cache_relation(5, 9, 4), "nenhum")

    def test_excel_serial_is_only_a_calendar_reading(self):
        self.assertEqual(excel_serial_calendar(2958465), date(9999, 12, 31))
        self.assertIsNone(excel_serial_calendar("2958465"))

    def test_base_row_preserves_source_values_and_ignores_caches(self):
        prepared = prepare_base_row(
            _row(
                material="MAT-1 ",
                center="C01",
                lrr=None,
                forecast="*",
                status="Roteiro setembro",
                observation="Texto da linha",
                quantity=-7,
                delivered_on=None,
                plant="APELIDO",
                estoque_parque=0,
                quant_po=750,
            ),
            8,
        )
        self.assertEqual(prepared["material"], "MAT-1 ")
        self.assertIsNone(prepared["lrr"])
        self.assertIsNone(prepared["forecast_on"])
        self.assertEqual(prepared["forecast_original"], "*")
        self.assertEqual(prepared["status"], "Roteiro setembro")
        self.assertEqual(prepared["observation"], "Texto da linha")
        self.assertIsNone(prepared["status_change"])
        self.assertEqual(prepared["delivery"]["quantity"], Decimal("-7"))
        self.assertIsNone(prepared["delivery"]["delivered_on"])
        self.assertTrue(prepared["delivery"]["requires_review"])
        self.assertEqual(prepared["delivery"]["source"], BASE_SOURCE)
        self.assertEqual(prepared["delivery"]["source_row"], 8)
        reasons = {note["motivo"] for note in prepared["revisoes"]}
        self.assertIn("espaco_preservado", reasons)
        self.assertIn("sem_destino", reasons)
        self.assertIn("cache_ignorado", reasons)
        self.assertNotIn("estoque_parque", prepared)
        self.assertNotIn("quant_po", prepared)

    def test_zero_quantity_stays_distinct_from_negative_and_from_absence(self):
        zero = prepare_base_row(_row(quantity=0, delivered_on=date(2026, 6, 15)), 3)
        absent = prepare_base_row(_row(quantity=None, delivered_on=None), 4)
        self.assertEqual(zero["delivery"]["quantity"], Decimal("0"))
        self.assertEqual(zero["delivery"]["delivered_on"], date(2026, 6, 15))
        self.assertFalse(zero["delivery"]["requires_review"])
        self.assertIsNone(absent["delivery"])

    def test_valid_forecast_date_stays_on_the_first_day(self):
        prepared = prepare_base_row(
            _row(forecast=datetime(2026, 8, 1, 0, 0), quantity=None),
            5,
        )
        self.assertEqual(prepared["forecast_on"], date(2026, 8, 1))
        self.assertEqual(prepared["forecast_original"], "")
        self.assertIsNone(prepared["delivery"])

    def test_origin_follows_the_source_row_and_not_the_item_key(self):
        first = delivery_origin(12)
        second = delivery_origin(13)
        again = delivery_origin(12)
        other_source = delivery_origin(12, source="outra-fonte")
        self.assertEqual(first, again)
        self.assertNotEqual(first, second)
        self.assertNotEqual(first, other_source)
        self.assertNotEqual(first, critical_key("MAT-1", "C01"))
        with self.assertRaises(PreparationError):
            delivery_origin(1)

    def test_two_rows_of_the_same_item_are_different_deliveries(self):
        first = prepare_base_row(_row(quantity=-7, delivered_on=None), 12)
        second = prepare_base_row(
            _row(quantity=-7, delivered_on=date(2026, 6, 15)),
            13,
        )
        self.assertNotEqual(
            (first["delivery"]["source"], first["delivery"]["source_row"]),
            (second["delivery"]["source"], second["delivery"]["source_row"]),
        )
        self.assertEqual(repeated_origins([first, second]), [])
        self.assertEqual(repeated_origins([first, first]), [(BASE_SOURCE, 12)])

    def test_reimport_recognizes_the_same_origin_without_an_update(self):
        prepared = prepare_base_row(_row(quantity=-7, delivered_on=None), 12)
        plan = plan_reimport(
            prepared,
            existing_item=_stored_item(prepared),
            existing_delivery=_stored_delivery(prepared, author="conta-teste"),
        )
        self.assertEqual(plan["item"], "item_existente")
        self.assertEqual(plan["entrega"], "entrega_conhecida")
        self.assertEqual(plan["acao"], "reconhecer")
        self.assertEqual(plan["divergencias"], [])
        self.assertIsNone(plan["atualizacao"])
        self.assertEqual(plan["preservado"]["autor"], "conta-teste")
        self.assertTrue(plan["preservado"]["historico_de_status"])
        self.assertTrue(REIMPORT_POLICY["confirmada"])
        self.assertEqual(REIMPORT_POLICY["nome"], "somente_relatar")
        self.assertEqual(REIMPORT_POLICY["atualiza_campos"], ())
        self.assertFalse(REIMPORT_POLICY["sobrescrita_silenciosa"])

    def test_known_origin_with_different_content_is_a_divergence(self):
        prepared = prepare_base_row(
            _row(quantity=4, delivered_on=date(2026, 7, 1), status="Em rota"),
            12,
        )
        stored = _stored_item(prepared)
        stored["status"] = "Pendente"
        stored["lrr"] = Decimal("0")
        plan = plan_reimport(
            prepared,
            existing_item=stored,
            existing_delivery={
                "source": BASE_SOURCE,
                "source_row": 12,
                "quantity": Decimal("-7.000"),
                "delivered_on": None,
                "author": "conta-teste",
                "material": prepared["material"],
                "center": prepared["center"],
            },
        )
        fields = {item["campo"] for item in plan["divergencias"]}
        self.assertEqual(plan["acao"], "revisar")
        self.assertEqual(plan["entrega"], "entrega_conhecida")
        self.assertIn("status", fields)
        self.assertIn("lrr", fields)
        self.assertIn("quantity", fields)
        self.assertIn("delivered_on", fields)
        self.assertIsNone(plan["atualizacao"])
        self.assertEqual(plan["preservado"]["autor"], "conta-teste")

    def test_new_item_and_new_delivery_are_distinct_from_an_existing_pair(self):
        prepared = prepare_base_row(_row(quantity=2, delivered_on=None), 20)
        self.assertEqual(plan_reimport(prepared)["item"], "novo_item")
        self.assertEqual(plan_reimport(prepared)["entrega"], "nova_entrega")
        self.assertEqual(plan_reimport(prepared)["acao"], "criar")
        existing = plan_reimport(
            prepared,
            existing_item=_stored_item(prepared),
        )
        self.assertEqual(existing["item"], "item_existente")
        self.assertEqual(existing["entrega"], "nova_entrega")

    def test_spacing_is_preserved_and_only_reported_as_collision(self):
        self.assertEqual(normalized_code("MAT-1 "), "MAT-1")
        self.assertEqual(read_material("MAT-1 "), "MAT-1 ")
        collisions = normalized_collisions(
            [("MAT-1", "C01"), ("MAT-1 ", "C02")]
        )
        self.assertEqual(len(collisions), 1)
        self.assertEqual(collisions[0]["originais"], ("MAT-1", "MAT-1 "))


def _row(**overrides):
    values = {
        "material": "MAT-1",
        "center": "C01",
        "description": "Descricao sintetica",
        "lrr": None,
        "forecast": date(2026, 8, 1),
        "status": "Pendente",
        "observation": "",
        "quantity": None,
        "delivered_on": None,
    }
    values.update(overrides)
    return values


def _stored_item(prepared):
    return {
        "material": prepared["material"],
        "center": prepared["center"],
        "description": prepared["description"],
        "lrr": prepared["lrr"],
        "forecast_on": prepared["forecast_on"],
        "forecast_original": prepared["forecast_original"],
        "status": prepared["status"],
        "observation": prepared["observation"],
    }


def _stored_delivery(prepared, author=None):
    delivery = prepared["delivery"]
    return {
        "source": delivery["source"],
        "source_row": delivery["source_row"],
        "quantity": delivery["quantity"],
        "delivered_on": delivery["delivered_on"],
        "author": author,
        "material": prepared["material"],
        "center": prepared["center"],
    }


