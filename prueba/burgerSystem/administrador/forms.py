from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombre', 'apellido', 'telefono', 'email', 'fecha_nacimiento', 'cedula', 'ciudad', 'barrio', 'nacionalidad', 'ruc'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Juan'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Perez'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0987654321'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'juanperez@gmail.com'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123456789'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Coronel Oviedo'}),
            'barrio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barrio Centro'}),
            'nacionalidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Paraguaya'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1234567-8'}),
        }