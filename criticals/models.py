from django.conf import settings
from django.db import models


class CriticalItem(models.Model):
    """Item da Base, identificado por material e centro.

    A descrição é a informada na linha. LRR vazio fica nulo e zero fica zero.
    A previsão em data guarda o dia 1. Um texto original, como ``*``, fica fora
    da data e não recebe significado. O status atual é texto livre; cada valor
    anterior fica em StatusChange.
    Os tamanhos e as casas decimais são teto técnico, não regra dos documentos.
    """

    material = models.CharField("material", max_length=40)
    center = models.CharField("centro", max_length=10)
    description = models.TextField("descrição original")
    # max_digits e decimal_places são teto técnico provisório.
    lrr = models.DecimalField(
        "LRR",
        max_digits=14,
        decimal_places=3,
        null=True,
        blank=True,
    )
    forecast_on = models.DateField("previsão", null=True, blank=True)
    forecast_original = models.TextField("previsão original", blank=True)
    status = models.CharField("status", max_length=80, blank=True)
    observation = models.TextField("observação", blank=True)

    class Meta:
        verbose_name = "item crítico"
        verbose_name_plural = "itens críticos"
        permissions = [
            (
                "change_critical_status",
                "Pode registrar alteração de status do item crítico",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("material", "center"),
                name="critical_item_material_center_uniq",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(forecast_on__isnull=True)
                    | models.Q(forecast_original="")
                ),
                name="critical_item_forecast_original_or_date",
            ),
        ]

    def __str__(self):
        return f"{self.material} {self.center}"


class StatusChange(models.Model):
    """Valor de status que precisa permanecer depois de uma troca.

    O texto legado não é convertido. Autor e instante ficam vazios quando a
    origem não os informa. A conta, se removida, não apaga o registro.
    """

    item = models.ForeignKey(
        CriticalItem,
        verbose_name="item crítico",
        related_name="status_changes",
        on_delete=models.CASCADE,
    )
    status = models.CharField("status", max_length=80)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="autor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="critical_status_changes",
    )
    changed_at = models.DateTimeField("instante", null=True, blank=True)

    class Meta:
        verbose_name = "alteração de status"
        verbose_name_plural = "alterações de status"

    def __str__(self):
        return f"{self.item} {self.status}"


class Delivery(models.Model):
    """Entrega de um item crítico.

    Um item pode ter várias. A quantidade negativa é conservada e sinalizada.
    A data pode faltar. O autor é opcional e aponta para um usuário existente.
    A entrega vinda da aba Base guarda a fonte e a linha original. Entrega
    lançada no sistema deixa os dois vazios. A origem está na migração
    ``0002_delivery_origin``.
    """

    item = models.ForeignKey(
        CriticalItem,
        verbose_name="item crítico",
        related_name="deliveries",
        on_delete=models.CASCADE,
    )
    # max_digits e decimal_places são teto técnico provisório.
    quantity = models.DecimalField(
        "quantidade entregue",
        max_digits=14,
        decimal_places=3,
    )
    delivered_on = models.DateField("data da entrega", null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="autor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="critical_deliveries",
    )
    source = models.CharField("fonte", max_length=80, blank=True)
    source_row = models.PositiveIntegerField(
        "linha de origem",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "entrega"
        verbose_name_plural = "entregas"
        constraints = [
            models.UniqueConstraint(
                fields=("source", "source_row"),
                condition=models.Q(source_row__isnull=False),
                name="delivery_source_row_uniq",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(source="", source_row__isnull=True)
                    | (
                        models.Q(source_row__isnull=False)
                        & ~models.Q(source="")
                    )
                ),
                name="delivery_source_pair",
            ),
        ]

    def __str__(self):
        return f"{self.item} {self.quantity}"

    @property
    def requires_review(self):
        """A quantidade negativa fica sinalizada e não é alterada."""
        return self.quantity < 0


class StockPosition(models.Model):
    """Posição de estoque ligada a um item pelo material e pelo centro exatos.

    Depósito e lote vazios fazem parte da posição. As quatro quantidades
    permanecem separadas. A carga real da aba não entra neste modelo até
    autorização própria.
    """

    item = models.ForeignKey(
        CriticalItem,
        verbose_name="item crítico",
        related_name="stock_positions",
        on_delete=models.CASCADE,
    )
    material = models.CharField("material", max_length=40)
    center = models.CharField("centro", max_length=10)
    center_name = models.CharField(
        "nome do centro na origem", max_length=120, blank=True
    )
    deposit = models.CharField("depósito", max_length=20, blank=True)
    deposit_description = models.CharField(
        "descrição do depósito na origem",
        max_length=120,
        blank=True,
    )
    lot = models.CharField("lote", max_length=20, blank=True)
    unit = models.CharField("unidade", max_length=10, blank=True)
    stock_description = models.TextField("texto breve do estoque", blank=True)
    unrestricted = models.DecimalField(
        "utilização livre",
        max_digits=14,
        decimal_places=3,
    )
    in_transit = models.DecimalField(
        "estoque em trânsito",
        max_digits=14,
        decimal_places=3,
    )
    in_quality = models.DecimalField(
        "em controle de qualidade",
        max_digits=14,
        decimal_places=3,
    )
    blocked = models.DecimalField(
        "bloqueado",
        max_digits=14,
        decimal_places=3,
    )
    source = models.CharField("fonte", max_length=80, blank=True)
    source_row = models.PositiveIntegerField(
        "linha de origem",
        null=True,
        blank=True,
    )
    source_file_sha256 = models.CharField(
        "SHA-256 do arquivo de origem", max_length=64, blank=True
    )
    content_sha256 = models.CharField(
        "SHA-256 da linha de origem", max_length=64, blank=True
    )

    class Meta:
        verbose_name = "posição de estoque"
        verbose_name_plural = "posições de estoque"
        constraints = [
            models.UniqueConstraint(
                fields=("source", "source_row"),
                condition=models.Q(source_row__isnull=False),
                name="stock_position_source_row_uniq",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(source="", source_row__isnull=True)
                    | (
                        models.Q(source_row__isnull=False)
                        & ~models.Q(source="")
                    )
                ),
                name="stock_position_source_pair",
            ),
        ]

    def __str__(self):
        return f"{self.material} {self.center} {self.deposit} {self.lot}"


class LinkedSheetRow(models.Model):
    """Linha original de SQVI/LRR ligada por material e centro exatos.

    Valores e fórmulas são mantidos como evidência da fonte. Esta tabela não
    interpreta recebimentos, saldos nem parâmetros MRP.
    """

    class Sheet(models.TextChoices):
        SQVI = "SQVI", "SQVI"
        LRR = "LRR", "LRR"

    item = models.ForeignKey(
        CriticalItem,
        verbose_name="item crítico correspondente",
        related_name="source_sheet_rows",
        on_delete=models.PROTECT,
    )
    sheet = models.CharField("aba de origem", max_length=8, choices=Sheet.choices)
    source_row = models.PositiveIntegerField("linha original da planilha")
    material = models.CharField("material original", max_length=40)
    center = models.CharField("centro original", max_length=10)
    raw_values = models.JSONField("valores originais", default=list)
    source_file_sha256 = models.CharField(
        "SHA-256 do arquivo de origem", max_length=64
    )
    content_sha256 = models.CharField("SHA-256 da linha de origem", max_length=64)

    class Meta:
        verbose_name = "linha de fonte vinculada"
        verbose_name_plural = "linhas de fontes vinculadas"
        ordering = ("sheet", "source_row")
        constraints = [
            models.UniqueConstraint(
                fields=("sheet", "source_row"),
                name="linked_sheet_source_row_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(source_row__gte=2),
                name="linked_sheet_source_row_data_only",
            ),
        ]

    def __str__(self):
        return f"{self.sheet} linha {self.source_row}: {self.material} {self.center}"
