import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.profiles import PROFILES


class Command(BaseCommand):
    help = (
        "Cria uma conta individual em um perfil, sem privilégio de superusuário."
    )

    def add_arguments(self, parser):
        parser.add_argument("--usuario", required=True)
        parser.add_argument("--perfil", required=True, choices=PROFILES)

    def handle(self, *args, **options):
        username = options["usuario"].strip()
        if not username:
            raise CommandError("Informe o identificador de login.")

        password = getpass.getpass("Senha: ")
        confirmation = getpass.getpass("Repita a senha: ")
        if password != confirmation:
            raise CommandError("As senhas não conferem.")
        if not password:
            raise CommandError("A senha não pode ficar vazia.")

        user_model = get_user_model()
        if user_model.objects.filter(username=username).exists():
            raise CommandError("Já existe uma conta com esse usuário.")

        candidate = user_model(username=username)
        try:
            validate_password(password, user=candidate)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages)) from exc

        try:
            group = Group.objects.get(name=options["perfil"])
        except Group.DoesNotExist as exc:
            raise CommandError(
                "O perfil ainda não existe. Aplique as migrações locais antes."
            ) from exc

        user = user_model.objects.create_user(username=username, password=password)
        user.groups.add(group)
        if user.is_superuser or user.is_staff:
            raise CommandError("A conta foi criada com privilégio não permitido.")

        self.stdout.write(
            self.style.SUCCESS(f"Conta criada no perfil {group.name}.")
        )
