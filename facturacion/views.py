from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Timbrado
from .forms import TimbradoForm

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