
window.addEventListener('modalProductoCerrado', () => {
    const modalEl = document.getElementById('modalProducto');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
        modal.hide();
    }
});

