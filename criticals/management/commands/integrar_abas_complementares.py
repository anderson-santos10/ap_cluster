"""Integra correspondências exatas de Est. Parq., SQVI e LRR.

O padrão é simulação. A opção explícita --confirmar-integracao grava somente
linhas novas, em transação, no PostgreSQL local apcluster.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from criticals.base_load import LoadRefused, confirm_local_database
from criticals.models import CriticalItem, Delivery, LinkedSheetRow, StockPosition
from criticals.source_integration import (
    APPROVED_WORKBOOK_SHA256,
    EXPECTED_MATCH_COUNTS,
    EXPECTED_MATCHED_ITEMS,
    OFFICIAL_WORKBOOK,
    STOCK_SOURCE,
    SourceIntegrationError,
    classify_existing_rows,
    file_sha256,
    model_instances,
    read_complementary_sheets,
)


class Command(BaseCommand):
    help = "Pré-valida ou integra correspondências exatas das abas complementares."

    def add_arguments(self, parser):
        parser.add_argument(
            "--origem",
            default=str(OFFICIAL_WORKBOOK),
            help="Deve ser o arquivo oficial localizado na raiz do projeto.",
        )
        parser.add_argument(
            "--confirmar-integracao",
            action="store_true",
            help="Grava somente linhas novas após todas as validações passarem.",
        )

    def handle(self, *args, **options):
        try:
            destination = confirm_local_database()
        except LoadRefused as exc:
            raise CommandError(str(exc)) from exc

        source = Path(options["origem"]).resolve()
        if source != OFFICIAL_WORKBOOK.resolve():
            raise CommandError(
                "A origem precisa ser a planilha oficial na raiz do projeto."
            )
        if not source.is_file():
            raise CommandError("A planilha oficial não foi encontrada.")

        items = list(CriticalItem.objects.all().order_by("pk"))
        if len(items) != 96:
            raise CommandError("O banco não contém os 96 itens críticos esperados.")
        items_by_key = {}
        for item in items:
            key = (item.material, item.center)
            if key in items_by_key:
                raise CommandError("Há chave material + centro repetida no banco.")
            items_by_key[key] = item

        try:
            prepared = read_complementary_sheets(source, items_by_key)
        except (OSError, SourceIntegrationError) as exc:
            raise CommandError(str(exc)) from exc

        if prepared.source_file_sha256 != APPROVED_WORKBOOK_SHA256:
            raise CommandError(
                "A planilha difere da versão aprovada. Gere e revise uma nova prévia."
            )
        for sheet, expected_count in EXPECTED_MATCH_COUNTS.items():
            actual = len(prepared.sheets[sheet].matched_rows)
            matched_items = len(prepared.sheets[sheet].matched_item_ids)
            if (
                actual != expected_count
                or matched_items != EXPECTED_MATCHED_ITEMS[sheet]
            ):
                raise CommandError(
                    f"A prévia de {sheet} difere do escopo validado; nada foi gravado."
                )

        existing_stock = list(
            StockPosition.objects.filter(
                source=STOCK_SOURCE,
                source_row__isnull=False,
            )
        )
        existing_linked = list(
            LinkedSheetRow.objects.filter(sheet__in=("SQVI", "LRR"))
        )
        planned, conflicts = classify_existing_rows(
            prepared,
            existing_stock,
            existing_linked,
        )

        self.stdout.write(
            f"banco {destination['name']} "
            f"{destination['address']}:{destination['port']}"
        )
        self.stdout.write(f"sha256 {prepared.source_file_sha256}")
        for sheet, source_data in prepared.sheets.items():
            states = [state for _row, state in planned[sheet]]
            self.stdout.write(
                f"{sheet}: linhas_origem={source_data.nonempty_rows} "
                f"correspondencias_exatas={len(source_data.matched_rows)} "
                f"itens_correspondentes={len(source_data.matched_item_ids)} "
                f"fora_do_recorte={source_data.excluded_rows} "
                f"novas={states.count('novo')} iguais={states.count('igual')}"
            )
        if conflicts:
            self.stdout.write("conflitos " + repr(conflicts))
            raise CommandError("Há conflitos de origem. Nenhum registro foi gravado.")

        stock_instances, linked_instances = model_instances(
            planned,
            prepared.source_file_sha256,
        )
        counts_before = _counts()
        if not options["confirmar_integracao"]:
            self.stdout.write("modo simulação; nenhum registro foi gravado")
            return

        if file_sha256(source) != prepared.source_file_sha256:
            raise CommandError("A planilha mudou após a prévia. Nada foi gravado.")

        with transaction.atomic():
            StockPosition.objects.bulk_create(stock_instances)
            LinkedSheetRow.objects.bulk_create(linked_instances)
            counts_after = _counts()
            expected_after = {
                **counts_before,
                "stock": counts_before["stock"] + len(stock_instances),
                "linked": counts_before["linked"] + len(linked_instances),
            }
            if counts_after != expected_after:
                raise CommandError("Contagens inesperadas; a transação foi revertida.")

        self.stdout.write(
            "criados "
            f"estoque={len(stock_instances)} "
            f"sqvi={sum(1 for row in linked_instances if row.sheet == 'SQVI')} "
            f"lrr={sum(1 for row in linked_instances if row.sheet == 'LRR')}"
        )
        self.stdout.write("contagens preservadas " + repr(counts_after))


def _counts():
    return {
        "items": CriticalItem.objects.count(),
        "deliveries": Delivery.objects.count(),
        "histories": CriticalItem._meta.apps.get_model(
            "criticals", "StatusChange"
        ).objects.count(),
        "stock": StockPosition.objects.count(),
        "linked": LinkedSheetRow.objects.count(),
    }
