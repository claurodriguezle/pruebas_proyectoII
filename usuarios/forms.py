from django import forms
from django.contrib.auth.models import User
from administrador.models import Persona, Direccion
from datetime import date

class RegistroClienteForm(forms.ModelForm):
    username = forms.CharField(
        label='Nombre de usuario',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    ruc = forms.CharField(
        label='RUC',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Persona
        fields = [
            'nombre', 'apellido', 'telefono', 'fecha_nacimiento',
            'cedula', 'ciudad', 'barrio', 'nacionalidad',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.Select(attrs={'class': 'form-select'}),
            'barrio': forms.Select(attrs={'class': 'form-select'}),
            'nacionalidad': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Las contraseñas no coinciden.")
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este correo electrónico.")
        return email
    
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        hoy = date.today()

        edad = hoy.year - fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
        )

        if edad < 14:
            raise forms.ValidationError(
                'La persona debe ser mayor de 14 años.'
            )
        
        return fecha_nacimiento

class DireccionForm(forms.ModelForm):
    class Meta:
        model = Direccion
        fields = [
            "nombre", "direccion_text", "latitud", "longitud", "es_principal"]
        
        widgets = {
            "latitud": forms.HiddenInput(),
            "longitud": forms.HiddenInput()
        }
    def clean_latitud(self):
        lat = self.cleaned_data.get("latitud")
        if lat is not None:
            return round(lat, 7)
        return lat

    def clean_longitud(self):
        lat = self.cleaned_data.get("longitud")
        if lat is not None:
            return round(lat, 7)
        return lat

