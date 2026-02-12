//console.log("JS de facturación cargado");
function toggleFacturacion() {
    const read = document.getElementById('facturacion-read');
    const edit = document.getElementById('facturacion-edit');

    read.classList.toggle('d-none');
    edit.classList.toggle('d-none');
}

function guardarFacturacion() {
    const nombre = document.getElementById('input-nombre').value;
    const documento = document.getElementById('input-documento').value;

    // Actualiza el texto visible
    document.getElementById('read-nombre').innerText = nombre;
    document.getElementById('read-documento').innerText = documento;

    // Volver a vista solo lectura
    document.getElementById('facturacion-edit').classList.add('d-none');
    document.getElementById('facturacion-read').classList.remove('d-none');
}