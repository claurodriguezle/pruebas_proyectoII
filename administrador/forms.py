from xml.dom import ValidationErr
from django.core.exceptions import ValidationError
from django import forms
from django.utils import timezone
from .models import Persona, Cliente, Empleado, Proveedor, Producto, CategoriaProducto, IngredienteProducto, Salario, TipoEmpleado, Mesa  # noqa: F401
from .models import Compra, DetalleCompra, Item
from datetime import date

class PersonaForm(forms.ModelForm):

    class Meta:
        model = Persona
        fields = [
            'nombre', 'apellido', 'telefono', 'fecha_nacimiento', 'cedula', 'ruc', 'correo', 'ciudad', 'barrio', 'nacionalidad'
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Juan'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Perez'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0987654321'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'},
            format='%Y-%m-%d'),
            'cedula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123456789'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123456789-0'}),
            'correo' : forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@example.com'}),
            'ciudad': forms.Select(attrs={'class': 'form-select'}),
            'barrio': forms.Select(attrs={'class': 'form-select'}),
            'nacionalidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Paraguaya'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # solo al crear, no al editar
            self.fields['nacionalidad'].initial = 'Paraguaya'

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

class EmpleadoForm(forms.ModelForm):
    class Meta: 
        model = Empleado
        fields = ['salario', 'fecha_contratacion', 'tipo']
        widgets = {
            'salario': forms.Select(attrs={'class': 'form-select'}),
            'fecha_contratacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'min': '2020-01-01'}, 
            format='%Y-%m-%d'),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def fecha_contratacion(self):
        fecha_contratacion = self.cleaned_data.get('fecha_contratacion')

        if fecha_contratacion and fecha_contratacion.year < 2020:
            raise ValidationError(
                "La fecha de contratación no puede ser anterior al año 2020."
            )

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre_empresa']
        widgets = {
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control'}),
        }

class RolForm(forms.Form):
    rol = forms.ChoiceField(
        choices=[
            ('', '---------'),
            ('cliente', 'Cliente'),
            #('empleado', 'Empleado'),
            ('proveedor', 'Proveedor'),
        ],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'rol-select'}),
        label='Rol'
    )

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
                'max': timezone.now().date().isoformat()
            }),
        }

    def clean_numero_factura(self):
        """Valida que no exista otra compra ACTIVA con el mismo número de factura"""
        numero_factura = self.cleaned_data.get('numero_factura')
        
        if not numero_factura:
            return numero_factura
        
        # Si es una edición, excluir la compra actual
        compra_actual = self.instance if self.instance.pk else None
        
        # Buscar otra compra ACTIVA con el mismo número
        compra_existente = Compra.objects.filter(
            numero_factura=numero_factura,
            estado='ACTIVA'
        ).exclude(pk=compra_actual.pk if compra_actual else None).first()
        
        if compra_existente:
            raise forms.ValidationError(
                f'Ya existe una compra ACTIVA con el número de factura "{numero_factura}". '
                f'Si la compra anterior fue anulada, este número ya puede ser reutilizado.'
            )
        
        return numero_factura

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
        fields = ['nombre_categ', 'tipo']
        widgets = {
            'nombre_categ': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            })
        }

# FORMULARIO DE INGREDIENTES

class IngredienteProductoForm(forms.ModelForm):
    class Meta:
        model = IngredienteProducto
        fields = ['item', 'cantidad']

#FORMULARIO DE MESAS
class MesaForm(forms.ModelForm):
    class Meta:
        model = Mesa
        fields = ['numero', 'capacidad', 'estado', 'activa', 'es_mostrador']
        widgets = {
            'numero':       forms.NumberInput(attrs={'class': 'form-control'}),
            'capacidad':    forms.NumberInput(attrs={'class': 'form-control'}),
            'estado':       forms.Select(attrs={'class': 'form-select'}),
            'activa':       forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'es_mostrador': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'numero':       'Número de mesa',
            'capacidad':    'Capacidad (personas)',
            'estado':       'Estado',
            'activa':       'Activa',
            'es_mostrador': 'Es mostrador',
        }