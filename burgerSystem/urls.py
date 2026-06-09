"""
URL configuration for burgerSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from django.conf import settings
from django.conf.urls.static import static

from django.shortcuts import render

def sin_permiso(request):
    return render(request, 'sin_permiso.html', status=403)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('administrador/', include('administrador.urls')),
    path('', RedirectView.as_view(url='/pedidos/'), name='inicio'),
    path('facturacion/', include('facturacion.urls')),
    path('pedidos/', include(('pedidos.urls', 'pedidos'), namespace='pedidos')),
    path('usuarios/', include('usuarios.urls')),
    path('caja/', include('caja.urls')),
    path('reportes/', include('reportes.urls', namespace='reportes')),
    path('sin-permiso/', sin_permiso, name='sin_permiso'),
    path('egresos/', include('egresos.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
