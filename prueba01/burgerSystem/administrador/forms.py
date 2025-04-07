from django import forms
from .models import Persona, Cliente, Empleado, Proveedor # noqa: F401
from .models import Compra, DetalleCompra, Item

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

#Formularios para compras
class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['nombre','tipo','unidad_medida']
class DetalleCompraForm(forms.ModelForm):
    class Meta:
        model = DetalleCompra
        fields = ['item','cantidad','precio_compra']

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['item'].queryset = Item.objects.all()

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['numero_factura','fecha','proveedor']
        widgets = {
            'fecha': forms.DateInput(attrs={'type':'date'}),
        }
class CompraCompletaForm(forms.Form):
    numero_factura = forms.CharField(max_length=50)
    fecha = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    proveedor = forms.ModelChoiceField(queryset=Proveedor.objects.all())

    #Campos para el detalle
    item = forms.ModelChoiceField(queryset=Item.objects.all())
    cantidad = forms.DecimalField(max_digits=10, decimal_places=2)
    precio_compra = forms.DecimalField(max_digits=10,decimal_places=2)