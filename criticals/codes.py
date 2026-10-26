"""Comparação de códigos sem alterar o valor original."""

from collections import defaultdict

from criticals.models import CriticalItem
from criticals.preparation import normalized_code


def material_collisions():
    grouped = defaultdict(set)
    for material in CriticalItem.objects.values_list("material", flat=True):
        grouped[normalized_code(material)].add(material)
    return [
        {"normalizado": key, "originais": tuple(sorted(originals))}
        for key, originals in sorted(grouped.items())
        if len(originals) > 1
    ]


def spacing_items():
    return [
        item
        for item in CriticalItem.objects.order_by("material", "center")
        if item.material != normalized_code(item.material)
    ]
