"""Leitura rastreável das abas complementares da fonte aprovada.

Somente correspondências exatas com CriticalItem são preparadas. Fórmulas,
caches, textos e espaços da origem são preservados; nada é calculado aqui.
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

from django.conf import settings

from criticals.models import LinkedSheetRow, StockPosition


OFFICIAL_WORKBOOK = Path(settings.BASE_DIR) / "Criticos Ap Cluster.xlsx"
APPROVED_WORKBOOK_SHA256 = (
    "777ede653828560abec0640dcd409a6bed051ebe39614dd29e0bce7ddcff5d06"
)
STOCK_SOURCE = "criticos-ap-cluster:Est. Parq."
EXPECTED_MATCH_COUNTS = {"Est. Parq.": 127, "SQVI": 40, "LRR": 72}
EXPECTED_MATCHED_ITEMS = {"Est. Parq.": 74, "SQVI": 28, "LRR": 72}

SHEET_SPECS = {
    "Est. Parq.": {
        "column_count": 13,
        "material_column": 5,
        "center_column": 1,
        "signature": {
            1: "Centro",
            2: "Nome 1",
            3: "Depósito",
            4: "Descrição do depósito",
            5: "Material",
            6: "Texto breve material",
            7: "UM básica",
            8: "Lote",
            9: "Utilização livre",
            10: "Estoque em trânsito",
            11: "Em contr.qualidade",
            12: "Bloqueado",
        },
    },
    "SQVI": {
        "column_count": 61,
        "material_column": 19,
        "center_column": 17,
        "signature": {
            7: "Tipo",
            9: "Doc.compra",
            10: "Item",
            11: "Fornecedor",
            17: "Cen.",
            19: "Material",
            21: "Qtd.pedido",
            22: "UMP",
        },
    },
    "LRR": {
        "column_count": 48,
        "material_column": 1,
        "center_column": 3,
        "signature": {
            1: "Material",
            2: "Área MRP",
            3: "Área MRP centro",
            5: "Tipo de MRP",
            6: "Planejador MRP",
            7: "Grupo MRP",
            8: "Ponto reabastec.",
            9: "Ciclo MRP",
            11: "Tamanho do lote MRP",
        },
    },
}

QUANTITY_COLUMNS = {
    "unrestricted": 9,
    "in_transit": 10,
    "in_quality": 11,
    "blocked": 12,
}


class SourceIntegrationError(ValueError):
    """A estrutura ou conteúdo da fonte não pode ser integrado com segurança."""


@dataclass
class PreparedSourceRow:
    sheet: str
    source_row: int
    material: str
    center: str
    item: object
    raw_values: list
    content_sha256: str
    stock_fields: dict


@dataclass
class PreparedSheet:
    sheet: str
    nonempty_rows: int
    matched_rows: list
    matched_item_ids: set
    excluded_rows: int
    rows_seen: set


@dataclass
class PreparedWorkbook:
    path: Path
    source_file_sha256: str
    sheets: dict


def read_complementary_sheets(path, items_by_key, *, require_official=True):
    """Prepara só Est. Parq., SQVI e LRR, sem qualquer escrita no banco."""
    from openpyxl import load_workbook

    path = Path(path).resolve()
    if require_official and path != OFFICIAL_WORKBOOK.resolve():
        raise SourceIntegrationError("Use somente o arquivo oficial do projeto.")

    before_hash = file_sha256(path)
    # A fonte é pequena o bastante para carregar em memória; o modo normal
    # fecha o ZIP do XLSX após a leitura e permite reabrir o arquivo no Windows.
    formula_book = load_workbook(path, read_only=False, data_only=False)
    value_book = load_workbook(path, read_only=False, data_only=True)
    try:
        required = set(SHEET_SPECS)
        if not required.issubset(formula_book.sheetnames):
            raise SourceIntegrationError("Uma das abas complementares não existe.")
        prepared = {}
        for sheet_name, spec in SHEET_SPECS.items():
            worksheet = formula_book[sheet_name]
            value_sheet = value_book[sheet_name]
            if worksheet.max_column != spec["column_count"]:
                raise SourceIntegrationError(
                    f"A estrutura da aba {sheet_name} mudou; gere uma nova prévia."
                )
            headers = next(worksheet.iter_rows(min_row=1, max_row=1, values_only=True))
            _validate_headers(sheet_name, headers, spec)
            cached_headers = next(
                value_sheet.iter_rows(min_row=1, max_row=1, values_only=True)
            )
            if tuple(headers) != tuple(cached_headers):
                raise SourceIntegrationError(
                    f"Cabeçalho inconsistente em {sheet_name}."
                )

            prepared[sheet_name] = _prepare_sheet(
                sheet_name,
                worksheet,
                value_sheet,
                headers,
                spec,
                items_by_key,
            )
    finally:
        formula_book.close()
        value_book.close()

    after_hash = file_sha256(path)
    if before_hash != after_hash:
        raise SourceIntegrationError("O arquivo mudou durante a leitura.")
    return PreparedWorkbook(path, after_hash, prepared)


def _prepare_sheet(sheet_name, worksheet, value_sheet, headers, spec, items_by_key):
    records = []
    matched_items = set()
    rows_seen = set()
    nonempty = 0
    excluded = 0

    source_rows = zip(
        worksheet.iter_rows(min_row=2, values_only=True),
        value_sheet.iter_rows(min_row=2, values_only=True),
    )
    for source_row, (formula_values, cached_values) in enumerate(source_rows, start=2):
        if not any(value is not None for value in formula_values):
            continue
        nonempty += 1
        rows_seen.add(source_row)
        material = _identifier(formula_values[spec["material_column"]])
        center = _identifier(formula_values[spec["center_column"]])
        item = items_by_key.get((material, center))
        if item is None:
            excluded += 1
            continue

        raw_values = _serialize_row(headers, formula_values, cached_values)
        content_hash = _content_sha256(raw_values)
        stock_fields = {}
        if sheet_name == "Est. Parq.":
            stock_fields = _stock_fields(formula_values)
        records.append(
            PreparedSourceRow(
                sheet=sheet_name,
                source_row=source_row,
                material=material,
                center=center,
                item=item,
                raw_values=raw_values,
                content_sha256=content_hash,
                stock_fields=stock_fields,
            )
        )
        matched_items.add(item.pk)

    return PreparedSheet(
        sheet=sheet_name,
        nonempty_rows=nonempty,
        matched_rows=records,
        matched_item_ids=matched_items,
        excluded_rows=excluded,
        rows_seen=rows_seen,
    )


def _validate_headers(sheet, headers, spec):
    if len(headers) != spec["column_count"]:
        raise SourceIntegrationError(f"Número de colunas inesperado em {sheet}.")
    for index, expected in spec["signature"].items():
        if headers[index] != expected:
            raise SourceIntegrationError(
                f"Cabeçalho inesperado em {sheet}, coluna {index + 1}."
            )


def _serialize_row(headers, formula_values, cached_values):
    serialized = []
    for index, (header, raw, cached) in enumerate(
        zip(headers, formula_values, cached_values)
    ):
        cell = {
            "column": _column_name(index + 1),
            "header": header,
        }
        if isinstance(raw, str) and raw.startswith("="):
            cell["formula"] = raw
            cell["cached_value"] = _serialize_value(cached)
        else:
            cell["value"] = _serialize_value(raw)
        serialized.append(cell)
    return serialized


def _serialize_value(value):
    if value is None:
        return {"type": "blank", "value": None}
    if isinstance(value, datetime):
        return {"type": "datetime", "value": value.isoformat()}
    if isinstance(value, date):
        return {"type": "date", "value": value.isoformat()}
    if isinstance(value, time):
        return {"type": "time", "value": value.isoformat()}
    if isinstance(value, bool):
        return {"type": "boolean", "value": value}
    if isinstance(value, int):
        return {"type": "integer", "value": value}
    if isinstance(value, float):
        return {"type": "number", "value": str(value)}
    if isinstance(value, Decimal):
        return {"type": "decimal", "value": format(value, "f")}
    if isinstance(value, str):
        return {"type": "text", "value": value}
    return {"type": type(value).__name__, "value": str(value)}


def _stock_fields(values):
    quantities = {}
    for field, index in QUANTITY_COLUMNS.items():
        value = values[index]
        if value is None or isinstance(value, bool):
            raise SourceIntegrationError(
                f"Quantidade vazia ou inválida na linha de estoque: {index + 1}."
            )
        try:
            quantities[field] = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise SourceIntegrationError(
                f"Quantidade inválida na linha de estoque: {index + 1}."
            ) from exc

    return {
        "center_name": _text(values[2]),
        "deposit": _text(values[3]),
        "deposit_description": _text(values[4]),
        "stock_description": _text(values[6]),
        "unit": _text(values[7]),
        "lot": _text(values[8]),
        **quantities,
    }


def _identifier(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _text(value):
    return "" if value is None else str(value)


def _column_name(number):
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _content_sha256(value):
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as workbook_file:
        for chunk in iter(lambda: workbook_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_existing_rows(prepared, existing_stock, existing_linked):
    """Classifica criação, reimportação idêntica e conflitos sem gravar."""
    result = {"Est. Parq.": [], "SQVI": [], "LRR": []}
    conflicts = []

    stock_by_row = {row.source_row: row for row in existing_stock}
    for source_row in prepared.sheets["Est. Parq."].matched_rows:
        existing = stock_by_row.get(source_row.source_row)
        if existing is None:
            result["Est. Parq."].append((source_row, "novo"))
        elif existing.content_sha256 == source_row.content_sha256:
            result["Est. Parq."].append((source_row, "igual"))
        else:
            conflicts.append(("Est. Parq.", source_row.source_row))

    linked_by_key = {(row.sheet, row.source_row): row for row in existing_linked}
    for sheet in ("SQVI", "LRR"):
        for source_row in prepared.sheets[sheet].matched_rows:
            existing = linked_by_key.get((sheet, source_row.source_row))
            if existing is None:
                result[sheet].append((source_row, "novo"))
            elif existing.content_sha256 == source_row.content_sha256:
                result[sheet].append((source_row, "igual"))
            else:
                conflicts.append((sheet, source_row.source_row))

    for existing in existing_stock:
        if (
            existing.source_row not in prepared.sheets["Est. Parq."].rows_seen
            or not any(
                row.source_row == existing.source_row
                for row in prepared.sheets["Est. Parq."].matched_rows
            )
        ):
            conflicts.append(("Est. Parq.", existing.source_row))
    for existing in existing_linked:
        sheet_data = prepared.sheets[existing.sheet]
        if (
            existing.source_row not in sheet_data.rows_seen
            or not any(
                row.source_row == existing.source_row
                for row in sheet_data.matched_rows
            )
        ):
            conflicts.append((existing.sheet, existing.source_row))

    return result, sorted(set(conflicts))


def model_instances(prepared_rows, source_file_sha256):
    """Converte somente os novos candidatos em instâncias ainda não salvas."""
    stock = []
    linked = []
    for row, state in prepared_rows["Est. Parq."]:
        if state != "novo":
            continue
        stock.append(
            StockPosition(
                item=row.item,
                material=row.material,
                center=row.center,
                source=STOCK_SOURCE,
                source_row=row.source_row,
                source_file_sha256=source_file_sha256,
                content_sha256=row.content_sha256,
                **row.stock_fields,
            )
        )
    for sheet in ("SQVI", "LRR"):
        for row, state in prepared_rows[sheet]:
            if state != "novo":
                continue
            linked.append(
                LinkedSheetRow(
                    item=row.item,
                    sheet=sheet,
                    source_row=row.source_row,
                    material=row.material,
                    center=row.center,
                    raw_values=row.raw_values,
                    source_file_sha256=source_file_sha256,
                    content_sha256=row.content_sha256,
                )
            )
    return stock, linked
