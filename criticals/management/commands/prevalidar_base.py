import hashlib
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from criticals.base_load import LoadRefused, confirm_local_database, preview_against_database, read_base_rows

DEFAULT_SOURCE = Path(r"C:\Users\Anderson\Documents\PROJETOS\CZC\Criticos Ap Cluster.xlsx")


class Command(BaseCommand):
    help = "Pré-valida somente a aba Base, sem gravar registros."

    def add_arguments(self, parser):
        parser.add_argument("--origem", default=str(DEFAULT_SOURCE))

    def handle(self, *args, **options):
        try:
            destination = confirm_local_database()
        except LoadRefused as exc:
            raise CommandError(str(exc)) from exc
        source = Path(options["origem"])
        if source.name != "Criticos Ap Cluster.xlsx":
            raise CommandError("A origem precisa ser Criticos Ap Cluster.xlsx.")
        before = _sha256(source)
        prepared, errors = read_base_rows(source)
        after = _sha256(source)
        if before != after:
            raise CommandError("A planilha mudou durante a leitura.")
        preview = preview_against_database(prepared)
        summary = preview["resumo"]
        self.stdout.write(f"banco {destination['name']} {destination['address']}:{destination['port']}")
        self.stdout.write(f"sha256 {before}")
        self.stdout.write(f"linhas_validas {len(prepared)}")
        self.stdout.write(f"erros {len(errors)}")
        for key in (
            "novo_item",
            "item_existente",
            "nova_entrega",
            "entrega_conhecida",
            "criar",
            "reconhecer",
            "revisar",
            "colisoes",
            "entregas_manuais_preservadas",
            "atualizados",
            "origens_repetidas",
        ):
            self.stdout.write(f"{key} {summary[key]}")
        self.stdout.write("centros " + ", ".join(summary["centros"]))
        for error in errors:
            self.stdout.write(f"erro linha {error['linha']}: {error['motivo']}")
        for collision in preview["colisoes"]:
            self.stdout.write(
                "colisao "
                + collision["normalizado"]
                + " "
                + ", ".join(repr(value) for value in collision["originais"])
            )
        self.stdout.write("nenhum registro foi gravado")


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
