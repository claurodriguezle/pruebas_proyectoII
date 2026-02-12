document.addEventListener('DOMContentLoaded', function() {
  // Manejar cierre de caja
  document.getElementById('cerrarCajaBtn')?.addEventListener('click', function(e) {
    e.preventDefault();
    
    if(confirm('¿Está seguro que desea cerrar la caja?')) {
      fetch("{% url 'caja:cerrar_caja' %}", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': '{{ csrf_token }}'
        }
      })
      .then(response => response.json())
      .then(data => {
        if(data.success) {
          window.location.reload();
        } else {
          alert('Error al cerrar caja: ' + (data.message || 'Error desconocido'));
        }
      })
      .catch(error => {
        console.error('Error:', error);
        alert('Error al cerrar caja');
      });
    }
  });
});