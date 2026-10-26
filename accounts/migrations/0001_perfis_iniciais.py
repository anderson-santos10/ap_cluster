from django.db import migrations

PROFILE_NAMES = ("Administração", "Compras", "Estoque/Operação")


def create_profiles(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    for name in PROFILE_NAMES:
        group_model.objects.get_or_create(name=name)


def remove_profiles(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    group_model.objects.filter(name__in=PROFILE_NAMES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_profiles, remove_profiles),
    ]
