
window.addEventListener('modalProductoCerrado', () => {
    const modalEl = document.getElementById('modalProducto');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
        modal.hide();
    }
});

document.body.addEventListener('htmx:beforeSwap', function(evt) {
    if (evt.detail.xhr.status === 422) {
        // Le decimos a htmx: esto no es un error, sí quiero que lo swapees
        evt.detail.shouldSwap = true;
        evt.detail.isError = false;
    }
});
