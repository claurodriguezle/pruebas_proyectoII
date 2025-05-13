from django.urls import path
from .import views

app_name = 'pedidos'

urlpatterns = [
    path('', views.index, name='index'),
    path('menu/', views.menu_productos, name='menu_productos'),
]