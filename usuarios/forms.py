from django import forms
from administrador.models import Persona, Direccion, Empleado, Cliente, TipoEmpleado, Ciudad, Barrio, Salario
from datetime import date
from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
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
            "nombre", "direccion_text", "barrio", "latitud", "longitud", "es_principal"]
        
        widgets = {
            "nombre": forms.TextInput(attrs={'class': 'form-control'}),
            'direccion_text': forms.TextInput(attrs={'class': 'form-control'}),
            'barrio': forms.Select(attrs={'class': 'form-select'}),
            "latitud": forms.HiddenInput(),
            "longitud": forms.HiddenInput()
        }
    def clean_latitud(self):
        lat = self.cleaned_data.get("latitud")
        if lat is not None:
            return round(lat, 7)
        return lat

    def clean_longitud(self):
        lng = self.cleaned_data.get("longitud")
        if lng is not None:
            return round(lng, 7)
        return lng

#Forms para roles de usuarios
class UsuarioAdminForm(forms.Form):
    """Formulario para crear/editar usuarios desde el panel de administrador."""
 
    # Datos del User de Django
    username = forms.CharField(
        label='Nombre de usuario',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label='Contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={
        'class': 'form-control', 
        'placeholder': 'Dejar vacío para no cambiar'})
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
 
    # Grupo / Rol
    grupo = forms.ModelChoiceField(
        label='Rol',
        queryset=Group.objects.all(),
        required=False,
        empty_label='-- Cliente (sin rol) --',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
 
    # Datos de Persona
    nombre = forms.CharField(
        label='Nombre',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    apellido = forms.CharField(
        label='Apellido',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    cedula = forms.CharField(
        label='Cédula',
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    telefono = forms.CharField(
        label='Teléfono',
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    fecha_nacimiento = forms.DateField(
        label='Fecha de nacimiento',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    nacionalidad = forms.CharField(
        label='Nacionalidad',
        max_length=100,
        initial='Paraguaya',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    ruc = forms.CharField(
        label='RUC',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    ciudad = forms.ModelChoiceField(
        label='Ciudad',
        queryset=Ciudad.objects.all().order_by('nombre'),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_ciudad_admin'})
    )
    barrio = forms.ModelChoiceField(
        label='Barrio',
        queryset=Barrio.objects.all().order_by('nombre'),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_barrio_admin'})
    )
 
    # Solo para empleados
    tipo_empleado = forms.ModelChoiceField(
        label='Tipo de empleado',
        queryset=TipoEmpleado.objects.all(),
        required=False,
        empty_label='-- Seleccionar tipo --',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    fecha_contratacion = forms.DateField(
    label='Fecha de contratación',
    required=False,
    widget=forms.DateInput(attrs={
        'class': 'form-control',
        'type': 'date',
        'min': '2020-01-01'
    })
)

    salario = forms.ModelChoiceField(
        label='Salario',
        queryset=Salario.objects.all().order_by('monto'),
        required=False,
        empty_label='-- Sin asignar --',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
 
    def __init__(self, *args, **kwargs):
        self.usuario_id = kwargs.pop('usuario_id', None)
        super().__init__(*args, **kwargs)
 
    def clean_username(self):
        username = self.cleaned_data.get('username')
        qs = User.objects.filter(username=username)
        if self.usuario_id:
            qs = qs.exclude(pk=self.usuario_id)
        if qs.exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username
 
    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if self.usuario_id:
            qs = qs.exclude(pk=self.usuario_id)
        if qs.exists():
            raise forms.ValidationError("Ya existe un usuario con este correo.")
        return email
 
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        qs = Persona.objects.filter(cedula=cedula)
        if self.usuario_id:
            try:
                user = User.objects.get(pk=self.usuario_id)
                # Excluir la persona del usuario actual
                try:
                    qs = qs.exclude(pk=user.empleado.persona.pk)
                except Empleado.DoesNotExist:
                    try:
                        qs = qs.exclude(pk=user.cliente.persona.pk)
                    except Cliente.DoesNotExist:
                        pass
            except User.DoesNotExist:
                pass
        if qs.exists():
            raise forms.ValidationError("Ya existe una persona con esta cédula.")
        return cedula
 
    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            if edad < 14:
                raise forms.ValidationError("La persona debe ser mayor de 14 años.")
        return fecha
 
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        grupo = cleaned_data.get('grupo')
 
        if p1 or p2:
            if p1 != p2:
                self.add_error('password2', 'Las contraseñas no coinciden.')
            elif p1:
                try:
                    validate_password(p1)
                except Exception as e:
                    self.add_error('password1', e)
 
        # Si el rol es Empleado, requerir tipo, fecha contratación y salario
        if grupo and grupo.name in ['Administrador', 'Cocina', 'Empleado']:
            if not cleaned_data.get('tipo_empleado'):
                self.add_error('tipo_empleado', 'Requerido para empleados.')
            if not cleaned_data.get('fecha_contratacion'):
                self.add_error('fecha_contratacion', 'Requerida para empleados.')
            if not cleaned_data.get('salario'):
                self.add_error('salario', 'Requerido para empleados.')
 
        # Contraseña requerida al crear (usuario_id = None)
        if not self.usuario_id and not p1:
            self.add_error('password1', 'La contraseña es obligatoria al crear un usuario.')
 
        return cleaned_data
 
 
class CambiarPasswordAdminForm(forms.Form):
    """Formulario para que el admin cambie la contraseña de cualquier usuario."""
    password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
 
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        if p1:
            try:
                validate_password(p1)
            except Exception as e:
                self.add_error('password1', e)
        return cleaned_data
 