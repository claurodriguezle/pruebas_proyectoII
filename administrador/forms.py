from xml.dom import ValidationErr
from django import forms
from django.utils import timezone
from .models import Persona, Cliente, Empleado, Proveedor, Producto, CategoriaProducto, IngredienteProducto # noqa: F401
from .models import Compra, DetalleCompra, Item

class PersonaForm(forms.ModelForm):
    TIPO_PERSONA_CHOICES = [
        ('cliente', 'Cliente'),
        ('empleado', 'Empleado'),
        ('proveedor', 'Proveedor'),
    ]

    tipo_persona = forms.ChoiceField(
        choices=TIPO_PERSONA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'tipo-persona'}),
        label="Rol"
    )

    class Meta:
        model = Persona
        fields = [
            'nombre', 'apellido', 'telefono', 'fecha_nacimiento', 'cedula', 'ciudad', 'barrio', 'nacionalidad'
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Juan'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Perez'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0987654321'}),
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

# Codigo para manejar los campos dinamicos

def clean(self):
    cleaned_data = super().clean()
    tipo_persona = cleaned_data.get('tipo_persona')
    ruc = cleaned_data.get('ruc', '').strip()

    # Limpiar campos no relevantes
    if tipo_persona == 'cliente':
        cleaned_data['sueldo'] = None
        cleaned_data['fecha_contratacion'] = None
        cleaned_data['t_empleado'] = None
        cleaned_data['nombre_empresa'] = None
        
        # Guardar como NULL si ruc está vacío
        if not ruc:
            cleaned_data['ruc'] = None
        else:
            # Validar unicidad manual del RUC entre clientes
            from .models import Cliente  # evitar import circular
            qs = Cliente.objects.filter(ruc=ruc)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('ruc', 'Ya existe un cliente con este RUC.')

    elif tipo_persona == 'empleado':
        cleaned_data['ruc'] = None
        cleaned_data['nombre_empresa'] = None

    elif tipo_persona == 'proveedor':
        cleaned_data['sueldo'] = None
        cleaned_data['fecha_contratacion'] = None
        cleaned_data['t_empleado'] = None

    return cleaned_data

# PRODUCTOS
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'codigo', 'nombre', 'precio', 'imagen', 'descripcion', 'estado', 'personalizable', 'categoria',
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese codigo',
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese nombre de producto'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese precio',
                'step': '0.01',
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripcion del producto',
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select',
            }),
            'personalizable': forms.Select(choices=[(True, 'Sí'), (False, 'No')], attrs={
                'class': 'form-select',
            }),

            'categoria': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is None or precio <= 0:
            raise forms.ValidationError("El precio debe ser mayor a cero.")
        return precio

#Formularios para compras
class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['nombre','tipo','unidad_medida']

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        #Validar longitud minima
        if len(nombre) < 3:
            raise ValidationErr('El nombre debe tener al menos 3 caracteres')
        return nombre
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
        fields = ['numero_factura', 'fecha', 'proveedor']
        widgets = {
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'max': timezone.now().date().isoformat()  # Establece el máximo como hoy
            }),
        }

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError("La fecha de compra no puede ser posterior a hoy.")
        return fecha
class CompraCompletaForm(forms.Form):
    numero_factura = forms.CharField(max_length=50)
    fecha = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    proveedor = forms.ModelChoiceField(queryset=Proveedor.objects.all())

    #Campos para el detalle
    item = forms.ModelChoiceField(queryset=Item.objects.all())
    cantidad = forms.DecimalField(max_digits=10, decimal_places=2)
    precio_compra = forms.DecimalField(max_digits=10,decimal_places=2)

# CATEGORIAS
class CategoriaProductoForm(forms.ModelForm):
    class Meta:
        model = CategoriaProducto
        fields = ['nombre_categ']
        widgets = {
            'nombre_categ': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            })
        }

# FORMULARIO DE INGREDIENTES

class IngredienteProductoForm(forms.ModelForm):
    class Meta:
        model = IngredienteProducto
        fields = ['item', 'cantidad']