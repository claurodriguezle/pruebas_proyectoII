from django import forms
from .models import Egreso


class EgresoForm(forms.ModelForm):

    class Meta:
        model = Egreso
        fields = [
            'fecha',
            'monto',
            'descripcion',
            'categoria',
            'proveedor',
            'numero_comprobante',
            'salio_de_caja',
        ]
        widgets = {
            'fecha': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                },
                format='%Y-%m-%d'
            ),
            'monto': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Monto en Gs.',
                    'min': 1,
                }
            ),
            'descripcion': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: Factura ANDE agosto',
                }
            ),
            'categoria': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'proveedor': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'numero_comprobante': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: 001-001-0000123 (opcional)',
                }
            ),
            'salio_de_caja': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                    'role': 'switch',
                }
            ),
        }
        labels = {
            'fecha': 'Fecha del gasto',
            'monto': 'Monto (Gs.)',
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'proveedor': 'Proveedor (opcional)',
            'numero_comprobante': 'N° Comprobante (opcional)',
            'salio_de_caja': '¿Este gasto salió de la caja?',
        }

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto and monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        return monto


class AnulacionForm(forms.Form):
    motivo_anulacion = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explicá brevemente el motivo de la anulación...',
            }
        ),
        label='Motivo de anulación',
        min_length=10,
        error_messages={
            'min_length': 'El motivo debe tener al menos 10 caracteres.',
            'required': 'El motivo es obligatorio para anular un egreso.',
        }
    )

class EgresoCompraForm(forms.Form):
    salio_de_caja = forms.BooleanField(
        required=False,
        label='¿Este gasto salió de la caja?',
        widget=forms.CheckboxInput(
            attrs={
                'class': 'form-check-input',
                'role': 'switch',
            }
        )
    )