from django import forms

from criticals.models import Delivery
from criticals.panel import ABSENT_STATUS, status_sort_key


class ItemFilterForm(forms.Form):
    material = forms.CharField(label="Material", required=False)
    descricao = forms.CharField(label="Descrição", required=False)
    centro = forms.CharField(label="Centro", required=False)
    status = forms.CharField(label="Status", required=False)


class PanelFilterForm(forms.Form):
    centro = forms.ChoiceField(label="Centro", required=False)
    status = forms.ChoiceField(label="Status", required=False)

    def __init__(self, *args, centers, statuses, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["centro"].choices = [("", "Todos os centros")] + [
            (center, center) for center in centers
        ]
        status_choices = [("", "Todos os status")]
        visible = sorted((status for status in statuses if status), key=status_sort_key)
        if "" in statuses:
            status_choices.append((ABSENT_STATUS, "ausente"))
        status_choices.extend((status, status) for status in visible)
        self.fields["status"].choices = status_choices


class DeliveryForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = ("quantity", "delivered_on")
        labels = {
            "quantity": "Quantidade",
            "delivered_on": "Data da entrega",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["delivered_on"].required = False


class StatusForm(forms.Form):
    status = forms.CharField(label="Novo status", max_length=80)
