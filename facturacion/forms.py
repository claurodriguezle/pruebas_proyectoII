# facturacion/forms.py
from django import forms
from .models import Timbrado, Factura


class TimbradoForm(forms.ModelForm):
    class Meta:
        model = Timbrado
        fields = '__all__'
        widgets = {
            'fecha_inicio_vigencia': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin_vigencia': forms.DateInput(attrs={'type': 'date'}),
        }

class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = '__all__'
        widgets = {
            'fecha_emision': forms.DateInput(attrs={'type': 'date'}),
        }