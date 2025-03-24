from django import forms
from .models import Persona, Cliente, Empleado, Proveedor # noqa: F401

class PersonaForm(forms.ModelForm):
    TIPO_PERSONA_CHOICES = [
        ('cliente', 'Cliente'),
        ('empleado', 'Empleado'),
        ('proveedor', 'Proveedor'),
    ]

    tipo_persona = forms.ChoiceField(
        choices=TIPO_PERSONA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'form-rol'}),
        label="Rol"
    )

    class Meta:
        model = Persona
        fields = [
            'nombre', 'apellido', 'telefono', 'email', 'fecha_nacimiento', 'cedula', 'ciudad', 'barrio', 'nacionalidad'
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
        }

    # Campos de Roles especificos
    ruc = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1234567-8'}),
        label="RUC"
    )
    sueldo = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '3000000'}),
        label="Sueldo"
    )
    fecha_contratacion = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Fecha de Contratación"
    )
    t_empleado = forms.CharField(
    required=False,
    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tipo de Empleado'}),
    label="Tipo de Empleado"
    )
    nombre_empresa = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mi Empresa S.A.'}),
        label="Empresa"
    )