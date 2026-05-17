function imprimirTabla({ titulo, filtrosHTML, selectorTabla = '#resultado-reporte .table' }) {
    const tablaOrigen = document.querySelector(selectorTabla);
    if (!tablaOrigen) { alert('No hay datos para imprimir.'); return; }

    const ahora = new Date();
    const fechaImpresion = ahora.toLocaleDateString('es-PY') + ' ' +
        ahora.toLocaleTimeString('es-PY', { hour: '2-digit', minute: '2-digit' });

    const ventana = window.open('', '_blank', 'width=900,height=700');

    // Clonar la tabla para no modificar la original
let tablaHTML = tablaOrigen.outerHTML;

    // Eliminar las celdas con barras y dejar solo el porcentaje
const parser = new DOMParser();
const doc = parser.parseFromString(tablaHTML, 'text/html');
doc.querySelectorAll('.d-flex.align-items-center.gap-2').forEach(celda => {
    const porcentaje = celda.querySelector('span') ? celda.querySelector('span').textContent : '';
    celda.parentElement.innerHTML = porcentaje;
});
tablaHTML = doc.querySelector('table').outerHTML;

    ventana.document.write(`
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>${titulo}</title>
            <style>
                body { font-family: Arial, sans-serif; font-size: 13px; color: #000; padding: 20px; }
                h2 { margin: 0 0 4px 0; font-size: 18px; }
                h3 { margin: 0 0 4px 0; font-size: 14px; font-weight: normal; }
                p  { margin: 2px 0; font-size: 12px; }
                hr { margin: 10px 0; border: none; border-top: 1px solid #000; }
                table { width: 100%; border-collapse: collapse; margin-top: 12px; }
                th, td { border: 1px solid #000; padding: 6px 8px; text-align: left; font-size: 12px; }
                th { background: #f0f0f0; font-weight: bold; }
                .text-end { text-align: right; }
                .footer { margin-top: 20px; font-size: 11px; text-align: center; color: #555; }
            </style>
        </head>
        <body>
            <h2>Reportes - Brother's Burger System</h2>
            <h3>${titulo}</h3>
            <p>${filtrosHTML}</p>
            <p>Impreso el: ${fechaImpresion}</p>
            <hr>
            ${tablaHTML}
            <div class="footer">Sistema de gestión — Burger System</div>
        </body>
        </html>
    `);
    ventana.document.close();
    ventana.focus();
    ventana.print();
}

document.getElementById('filtros-form').addEventListener('htmx:confirm', function(e) {
    const fechaInicio = document.getElementById('fecha_inicio').value;
    const fechaFin    = document.getElementById('fecha_fin').value;
    const hoy         = new Date().toISOString().split('T')[0];

    let error = '';

    if (fechaInicio && fechaFin && fechaInicio > fechaFin) {
        error = 'La fecha de inicio no puede ser mayor que la fecha de fin.';
    } else if (fechaFin && fechaFin > hoy) {
        error = 'La fecha de fin no puede ser mayor a la fecha de hoy.';
    }

    if (error) {
        e.preventDefault();
        document.getElementById('error-fechas-msg').textContent = error;
        document.getElementById('error-fechas').classList.remove('d-none');
    } else {
        document.getElementById('error-fechas').classList.add('d-none');
    }
});