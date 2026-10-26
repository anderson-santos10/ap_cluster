"""Transformações da futura importação.

Estas funções não abrem a planilha e não gravam o banco. A chave do item
crítico continua sendo material + centro. Documento e item identificam uma
movimentação. Nenhuma das duas chaves autoriza somar saldo nem recebimento.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation


STOCK_QUANTITY_FIELDS = (
    "utilizacao_livre",
    "transito",
    "qualidade",
    "bloqueado",
)

UNKNOWN_STOCK = "desconhecido"


class PreparationError(ValueError):
    """Valor que a transformação não consegue representar com segurança."""


def text_from_code(value):
    """Converte código numérico em texto e preserva o texto já digitado."""
    if value is None:
        return ""
    if isinstance(value, bool):
        raise PreparationError("código lógico não é material nem centro")
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return format(value, "f")
    if isinstance(value, int):
        return str(value)
    return str(value)


def read_material(value):
    material = text_from_code(value)
    if material.strip() == "":
        raise PreparationError("material vazio")
    if len(material) > 40:
        raise PreparationError("material acima do teto técnico")
    return material


def read_center(value):
    center = text_from_code(value)
    if center.strip() == "":
        raise PreparationError("centro vazio")
    if len(center) > 10:
        raise PreparationError("centro acima do teto técnico")
    return center


def critical_key(material, center):
    return (read_material(material), read_center(center))


def movement_key(document, item):
    document_text = text_from_code(document).strip()
    item_text = text_from_code(item).strip()
    if document_text == "" or item_text == "":
        raise PreparationError("movimentação sem documento ou item")
    return (document_text, item_text)


def read_lrr(value):
    """Vazio permanece vazio. Zero permanece zero."""
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PreparationError("LRR não numérico") from exc


def read_forecast(value):
    """Data fica na data. Qualquer outro valor fica no texto original."""
    if value is None:
        return None, ""
    if isinstance(value, str) and value.strip() == "":
        return None, ""
    if isinstance(value, datetime):
        return value.date(), ""
    if isinstance(value, date):
        return value, ""
    return None, text_from_code(value)


def read_delivery(quantity, delivered_on):
    """Sem quantidade não há entrega. Data ausente ou serial não é inventada."""
    if quantity is None or (isinstance(quantity, str) and quantity.strip() == ""):
        if delivered_on not in (None, "") and not (
            isinstance(delivered_on, str) and delivered_on.strip() == ""
        ):
            raise PreparationError("data de entrega sem quantidade")
        return None
    try:
        parsed_quantity = Decimal(str(quantity))
    except (InvalidOperation, ValueError) as exc:
        raise PreparationError("quantidade entregue não numérica") from exc
    if isinstance(delivered_on, datetime):
        parsed_date = delivered_on.date()
    elif isinstance(delivered_on, date):
        parsed_date = delivered_on
    elif delivered_on is None or (
        isinstance(delivered_on, str) and delivered_on.strip() == ""
    ):
        parsed_date = None
    else:
        raise PreparationError("data de entrega não é uma data")
    return {
        "quantity": parsed_quantity,
        "delivered_on": parsed_date,
        "requires_review": parsed_quantity < 0,
    }


BASE_SOURCE = "criticos-ap-cluster:Base"

ITEM_COMPARE_FIELDS = (
    "description",
    "lrr",
    "forecast_on",
    "forecast_original",
    "status",
    "observation",
)

DELIVERY_COMPARE_FIELDS = ("quantity", "delivered_on")

IGNORED_BASE_FIELDS = (
    "estoque_parque",
    "estoque_ok",
    "quant_po",
    "conc",
    "mes_ano",
    "coluna_mes",
    "coluna_ano",
)

REIMPORT_POLICY = {
    "confirmada": True,
    "nome": "somente_relatar",
    "sobrescrita_silenciosa": False,
    "atualiza_campos": (),
    "campos_comparados_no_item": ITEM_COMPARE_FIELDS,
    "campos_comparados_na_entrega": DELIVERY_COMPARE_FIELDS,
    "preservar": (
        "historico_de_status",
        "autor_da_entrega",
        "entregas_sem_fonte",
    ),
}


def normalized_code(value):
    """Chave só para comparação. O código original não é alterado."""
    return text_from_code(value).strip()


def normalized_collisions(entries):
    """Não une registros. Aponta originais diferentes com a mesma comparação."""
    grouped = {}
    for material, center in entries:
        grouped.setdefault(normalized_code(material), []).append((material, center))
    collisions = []
    for key, members in grouped.items():
        originals = {material for material, _center in members}
        if len(originals) > 1:
            collisions.append(
                {
                    "normalizado": key,
                    "originais": tuple(sorted(originals)),
                    "ocorrencias": tuple(members),
                }
            )
    return collisions


def delivery_origin(row_number, source=BASE_SOURCE):
    """Fonte e linha original. Não usa material, centro, quantidade nem data."""
    if isinstance(row_number, bool) or not isinstance(row_number, int) or row_number < 2:
        raise PreparationError("linha de origem inválida")
    if not isinstance(source, str) or source.strip() == "":
        raise PreparationError("fonte inválida")
    return source, row_number


def prepare_base_row(values, row_number, source=BASE_SOURCE):
    """Transforma uma linha sintética ou lida da Base. Não grava nada."""
    material = read_material(values.get("material"))
    center = read_center(values.get("center"))
    description = text_from_code(values.get("description"))
    observation = text_from_code(values.get("observation"))
    status = text_from_code(values.get("status"))
    if len(status) > 80:
        raise PreparationError("status acima do teto técnico")
    forecast_on, forecast_original = read_forecast(values.get("forecast"))
    delivery = read_delivery(values.get("quantity"), values.get("delivered_on"))
    if delivery is not None:
        origin_source, origin_row = delivery_origin(row_number, source)
        delivery = {
            **delivery,
            "source": origin_source,
            "source_row": origin_row,
        }
    notes = _identifier_notes("material", material)
    notes.extend(_identifier_notes("centro", center))
    if description == "":
        notes.append({"campo": "descricao", "motivo": "vazia"})
    plant = text_from_code(values.get("plant"))
    if plant != "":
        notes.append({"campo": "planta", "motivo": "sem_destino", "valor": plant})
    for field in IGNORED_BASE_FIELDS:
        if field in values and values.get(field) not in (None, ""):
            notes.append({"campo": field, "motivo": "cache_ignorado"})
    return {
        "material": material,
        "center": center,
        "description": description,
        "lrr": read_lrr(values.get("lrr")),
        "forecast_on": forecast_on,
        "forecast_original": forecast_original,
        "status": status,
        "observation": observation,
        "delivery": delivery,
        "status_change": None,
        "revisoes": notes,
    }


def repeated_origins(prepared_rows):
    """Origens repetidas no mesmo lote. A unicidade do banco continua valendo."""
    seen = set()
    repeated = []
    for prepared in prepared_rows:
        delivery = prepared.get("delivery")
        if delivery is None:
            continue
        key = (delivery["source"], delivery["source_row"])
        if key in seen:
            repeated.append(key)
        seen.add(key)
    return repeated


def plan_reimport(prepared, existing_item=None, existing_delivery=None):
    """Reconhece item e entrega. Não grava e não monta atualização."""
    divergences = []
    if existing_item is None:
        item_state = "novo_item"
    else:
        item_state = "item_existente"
        for field in ITEM_COMPARE_FIELDS:
            if not _same_value(existing_item.get(field), prepared.get(field)):
                divergences.append(
                    {
                        "campo": field,
                        "atual": existing_item.get(field),
                        "origem": prepared.get(field),
                    }
                )
    incoming = prepared.get("delivery")
    if incoming is None:
        delivery_state = None
    elif existing_delivery is None:
        delivery_state = "nova_entrega"
    else:
        delivery_state = "entrega_conhecida"
        for field in DELIVERY_COMPARE_FIELDS:
            if not _same_value(existing_delivery.get(field), incoming.get(field)):
                divergences.append(
                    {
                        "campo": field,
                        "atual": existing_delivery.get(field),
                        "origem": incoming.get(field),
                    }
                )
        stored_item = (
            existing_delivery.get("material"),
            existing_delivery.get("center"),
        )
        if stored_item != (None, None) and stored_item != (
            prepared["material"],
            prepared["center"],
        ):
            divergences.append(
                {
                    "campo": "item_da_entrega",
                    "atual": stored_item,
                    "origem": (prepared["material"], prepared["center"]),
                }
            )
    if divergences:
        action = "revisar"
    elif item_state == "novo_item":
        action = "criar"
    else:
        action = "reconhecer"
    preserved_author = None
    if existing_delivery is not None:
        preserved_author = existing_delivery.get("author")
    return {
        "item": item_state,
        "entrega": delivery_state,
        "divergencias": divergences,
        "acao": action,
        "atualizacao": None,
        "preservado": {
            "autor": preserved_author,
            "historico_de_status": True,
            "entregas_sem_fonte": True,
        },
    }


def missing_stock():
    """Material ausente do extrato não vira zero."""
    return UNKNOWN_STOCK


def classify_position_group(rows):
    """Classifica cópia ou conflito. Não escolhe nem devolve um saldo."""
    prepared = [dict(row) for row in rows]
    if not prepared:
        raise PreparationError("grupo de estoque vazio")
    signatures = [_signature(row) for row in prepared]
    if len(prepared) == 1:
        situation = "unica"
        divergent = []
    elif len(set(signatures)) == 1:
        situation = "copia_identica"
        divergent = []
    else:
        situation = "conflito"
        divergent = _divergent_fields(prepared)
    return {
        "situacao": situation,
        "ocorrencias": len(prepared),
        "campos_divergentes": divergent,
        "efeito_se_somar": _quantity_sums(prepared),
        "saldo_resolvido": None,
    }


def referenced_base_row(formula):
    marker = "Base!A"
    if marker not in formula:
        raise PreparationError("fórmula sem critério na Base")
    digits = formula.split(marker, 1)[1].split(",", 1)[0]
    if not digits.isdigit():
        raise PreparationError("fórmula sem linha numérica")
    return int(digits)


def po_cache_relation(cache, own_sum, referenced_sum):
    """Diz qual soma o cache acompanha. Não transforma o cache em saldo."""
    cache_value = Decimal(str(cache or 0))
    own = Decimal(str(own_sum))
    referenced = Decimal(str(referenced_sum))
    if own == referenced:
        return "empate"
    if cache_value == referenced:
        return "segue_referencia"
    if cache_value == own:
        return "segue_linha"
    return "nenhum"


def descriptions_for_review(base_text, other_texts):
    """Registra os textos diferentes e não escolhe um deles."""
    others = tuple(other_texts)
    if not others or base_text in others:
        return ()
    return (base_text,) + others


def excel_serial_calendar(value):
    """Traduz um serial do Excel só para inspeção. Não autoriza gravação."""
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return date(1899, 12, 30) + timedelta(days=value)


def _identifier_notes(field, value):
    notes = []
    if value != value.strip():
        notes.append({"campo": field, "motivo": "espaco_preservado", "valor": value})
    if value[:1] == "0":
        notes.append(
            {"campo": field, "motivo": "zero_a_esquerda_preservado", "valor": value}
        )
    return notes


def _same_value(left, right):
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, Decimal) or isinstance(right, Decimal):
        try:
            return Decimal(left).quantize(Decimal("0.001")) == Decimal(right).quantize(
                Decimal("0.001")
            )
        except (InvalidOperation, ValueError):
            return False
    return left == right


def _blank(value):
    if value is None:
        return ""
    return str(value)


def _signature(row):
    return tuple(sorted((key, _blank(value)) for key, value in row.items()))


def _divergent_fields(rows):
    fields = []
    keys = sorted({key for row in rows for key in row})
    for key in keys:
        values = {_blank(row.get(key)) for row in rows}
        if len(values) > 1:
            fields.append(key)
    return fields


def _quantity_sums(rows):
    totals = {}
    for field in STOCK_QUANTITY_FIELDS:
        total = Decimal("0")
        seen = False
        for row in rows:
            if field not in row:
                continue
            seen = True
            value = row.get(field)
            total += Decimal(str(0 if value in (None, "") else value))
        if seen:
            totals[field] = total
    return totals
