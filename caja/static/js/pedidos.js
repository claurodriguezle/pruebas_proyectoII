// Gestión de pedidos
const currentOrder = {
  items: [],
  client: null,
  total: 0
};

function addToOrder(productName, price) {
  currentOrder.items.push({ productName, price });
  updateOrderSummary();
}

function updateOrderSummary() {
  const itemsList = document.getElementById('items-list');
  const totalAmount = document.getElementById('total-amount');
  
  // Calcular total
  currentOrder.total = currentOrder.items.reduce((sum, item) => sum + item.price, 0);
  
  // Actualizar UI
  if(currentOrder.items.length === 0) {
    itemsList.innerHTML = '<p class="empty-message">No hay productos agregados</p>';
  } else {
    itemsList.innerHTML = currentOrder.items.map(item => `
      <div class="order-item">
        <span>${item.productName}</span>
        <span>$${item.price.toFixed(2)}</span>
      </div>
    `).join('');
  }
  
  totalAmount.textContent = `$${currentOrder.total.toFixed(2)}`;
}

// Event listener para confirmar pedido
document.getElementById('confirm-order')?.addEventListener('click', () => {
  const clientName = document.getElementById('client-name').value;
  
  if(!clientName) {
    alert('Por favor ingrese el nombre del cliente');
    return;
  }
  
  if(currentOrder.items.length === 0) {
    alert('Debe agregar al menos un producto');
    return;
  }
  
  // Registrar como ingreso en caja
  CajaManager.addMovement('ingreso', `Pedido de ${clientName}`, currentOrder.total);
  
  alert(`Pedido confirmado por $${currentOrder.total.toFixed(2)}`);
  window.location.href = 'caja_abierta.html';
});