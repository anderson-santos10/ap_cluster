from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from criticals.base_load import (
    LoadRefused,
    apply_prepared,
    confirm_local_database,
    read_base_rows,
)

DEFAULT_SOURCE = Path(r"C:\Users\Anderson\Documents\Criticos Ap Cluster.xlsx")


class Command(BaseCommand):
    help = "Carga futura da aba Base. Recusada sem autorização explícita."

    def add_arguments(self, parser):
        parser.add_argument("--origem", default=str(DEFAULT_SOURCE))
        parser.add_argument(
            "--autorizar-carga",
            action="store_true",
            help="Exige autorização explícita em uma execução futura. Não usar nesta etapa.",
        )

    def handle(self, *args, **options):
        try:
            confirm_local_database()
        except LoadRefused as exc:
            raise CommandError(str(exc)) from exc
        if not options["autorizar_carga"]:
            raise CommandError(
                "A carga real está bloqueada. Execute prevalidar_base. "
                "A importação só pode ocorrer com autorização explícita em uma solicitação futura."
            )
        source = Path(options["origem"])
        if source.name != "Criticos Ap Cluster.xlsx":
            raise CommandError("A origem precisa ser Criticos Ap Cluster.xlsx.")
        prepared, errors = read_base_rows(source)
        if errors:
            raise CommandError("A pré-validação encontrou linhas inválidas. Nada foi gravado.")
        result = apply_prepared(prepared, authorized=True)
        for key, value in result.items():
            self.stdout.write(f"{key} {value}")
