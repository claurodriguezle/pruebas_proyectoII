from django.shortcuts import redirect,render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import DetailView
from .models import Timbrado, Factura,DetalleFactura
from .forms import TimbradoForm, FacturaForm

# Create your views here.
# facturacion/views.py
class TimbradoListView(ListView):
    model = Timbrado
    template_name = 'timbrado/timbrado_list.html'
    context_object_name = 'timbrados'
    def get_queryset(self):
        # Solo muestra timbrados NO eliminados
        return Timbrado.objects.filter(eliminado=False)
class TimbradoCreateView(CreateView):
    model = Timbrado
    form_class = TimbradoForm
    template_name = 'timbrado/timbrado_form.html'
    success_url = reverse_lazy('facturacion:timbrado_list')

    def form_valid(self, form):
        messages.success(self.request, "✅ Timbrado creado correctamente.")
        return super().form_valid(form)

class TimbradoUpdateView(UpdateView):
    model = Timbrado
    form_class = TimbradoForm
    template_name = 'timbrado/timbrado_form.html'
    success_url = reverse_lazy('facturacion:timbrado_list')

    def form_valid(self, form):
        messages.success(self.request, "✏️ Timbrado actualizado correctamente.")
        return super().form_valid(form)

def timbrado_toggle_active(request, pk):
    timbrado = get_object_or_404(Timbrado, pk=pk)
    timbrado.activo = not timbrado.activo
    timbrado.save()
    messages.success(request, f"✅ Timbrado {'activado' if timbrado.activo else 'desactivado'} correctamente.")
    return redirect('facturacion:timbrado_list')

def timbrado_soft_delete(request, pk):
    timbrado = get_object_or_404(Timbrado, pk=pk)
    timbrado.soft_delete()  # Usamos el método que creamos
    messages.success(request, "Timbrado marcado como eliminado (no se borró de la BD).")
    return redirect('facturacion:timbrado_list')

#Vistas para Factura
def factura_view(request):
    # Buscar una factura activa, si existe
    #factura = Factura.objects.get(pk=factura_id)
    timbrado_activo = Timbrado.objects.filter(activo=True, eliminado=False).first()

    context = {
        'factura': None,
        'timbrado': timbrado_activo
    }
    return render(request, 'factura/factura.html', context)
