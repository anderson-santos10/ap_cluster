from django.db import migrations

VIEW_CODENAMES = ("view_criticalitem", "view_delivery", "view_statuschange")
STOCK_CODENAMES = VIEW_CODENAMES + ("add_delivery",)
ADMIN_CODENAMES = VIEW_CODENAMES + ("view_user", "add_user", "change_user")

PERMISSIONS = (
    ("criticals", "criticalitem", "view_criticalitem", "Can view item crítico"),
    ("criticals", "delivery", "view_delivery", "Can view entrega"),
    ("criticals", "delivery", "add_delivery", "Can add entrega"),
    ("criticals", "statuschange", "view_statuschange", "Can view alteração de status"),
    ("auth", "user", "view_user", "Can view user"),
    ("auth", "user", "add_user", "Can add user"),
    ("auth", "user", "change_user", "Can change user"),
)

ASSIGNMENTS = {
    "Compras": VIEW_CODENAMES,
    "Estoque/Operação": STOCK_CODENAMES,
    "Administração": ADMIN_CODENAMES,
}


def grant_permissions(apps, schema_editor):
    content_type_model = apps.get_model("contenttypes", "ContentType")
    permission_model = apps.get_model("auth", "Permission")
    group_model = apps.get_model("auth", "Group")
    stored = {}
    for app_label, model, codename, name in PERMISSIONS:
        content_type, _created = content_type_model.objects.get_or_create(
            app_label=app_label,
            model=model,
        )
        permission, _created = permission_model.objects.get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": name},
        )
        stored[codename] = permission
    for group_name, codenames in ASSIGNMENTS.items():
        group, _created = group_model.objects.get_or_create(name=group_name)
        group.permissions.add(*(stored[codename] for codename in codenames))


def revoke_permissions(apps, schema_editor):
    permission_model = apps.get_model("auth", "Permission")
    group_model = apps.get_model("auth", "Group")
    codenames = [item[2] for item in PERMISSIONS]
    permissions = permission_model.objects.filter(codename__in=codenames)
    for group in group_model.objects.filter(name__in=ASSIGNMENTS):
        group.permissions.remove(*permissions)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_perfis_iniciais"),
        ("criticals", "0003_critical_status_permission"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(grant_permissions, revoke_permissions),
    ]
