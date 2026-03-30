from django import forms
from datetime import time, timedelta
from django.utils import timezone

class RetiroForm(forms.Form):
    tipo_entrega = forms.CharField(widget=forms.HiddenInput(), initial='RE')
    hora_retiro = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'min': '19:00',
            #'max': '23:00'
            }),
        label='Hora estimada'
    )

    def clean_hora_retiro(self):
        hora = self.cleaned_data['hora_retiro']
        ahora = timezone.localtime().time() # Hora Paraguay
        minimo = (timezone.localtime() + timedelta(minutes=10)).time()

        if hora < time(19, 0) or hora > time(23, 0):
            raise forms.ValidationError("La hora debe estar entre las 19:00 y las 23:00.")
        if hora <= ahora:
            raise forms.ValidationError(
                "Debe seleccionar una hora con al menos 10 minutos de anticipación."
                f"La hora minima ahora es {minimo.strftime('%H:%M')}"
                )
        return hora
