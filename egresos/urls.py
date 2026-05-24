from django.urls import path
from . import views

app_name = 'egresos'

urlpatterns = [
    path('', views.lista_egresos, name='lista_egresos'),
    path('crear/', views.crear_egreso, name='crear_egreso'),
    path('editar/<int:pk>/', views.editar_egreso, name='editar_egreso'),
    path('anular/<int:pk>/', views.anular_egreso, name='anular_egreso'),
    path('registrar-compra/<int:compra_pk>/', views.registrar_compra_como_egreso,name='registrar_compra_como_egreso'),
]