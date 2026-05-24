
from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # ── Autenticación pública ──────────────────────────────────────────────
    path('sesion/',              views.iniciar_sesion,       name='sesion'),
    path('registro/',            views.registro_cliente,     name='registro'),
    path('exit/',                views.exit,                 name='exit'),

    # ── Perfil del usuario logueado (cliente) ─────────────────────────────
    path('perfil/',              views.perfil_user,          name='perfil_user'),
    path('perfil/editar/',       views.editar_perfil_cliente, name='editar_perfil'),
    path('perfil/eliminar/',     views.eliminar_cuenta,      name='eliminar_cuenta'),

    # ── Direcciones del cliente ───────────────────────────────────────────
    path('crear_direccion/',                     views.agregar_direccion,  name='crear_direccion'),
    path('direcciones/',                         views.listar_direcciones, name='listar_direc'),
    path('direcciones/<int:pk>/editar/',         views.editar_direccion,   name='editar_direccion'),
    path('direcciones/<int:pk>/eliminar/',       views.eliminar_direccion, name='eliminar_direccion'),

    # ── Gestión de usuarios (panel administrador) ─────────────────────────
    path('usuarios/',                            views.index,                  name='index'),
    path('usuarios/crear/',                      views.crear_usuario_admin,    name='crear'),
    path('usuarios/<int:pk>/editar/',            views.editar_usuario_admin,   name='editar'),
    path('usuarios/<int:pk>/toggle/',            views.toggle_activo,          name='toggle'),
    path('usuarios/<int:pk>/password/',          views.cambiar_password_admin, name='cambiar_password'),
]