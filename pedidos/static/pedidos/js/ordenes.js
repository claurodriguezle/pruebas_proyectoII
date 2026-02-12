// Datos de ejemplo CORREGIDOS
const orders = [
    {
        id: "#BB-243",
        total: "$87.00",
        customer: "Libra a Anna",
        paymentStatus: "paid",
        fulfillmentStatus: "cancelled",
        deliveryType: "Delivery",
        date: "12 de diciembre, 12:56 p.m.",
        items: ["Hamburguesa Clásica x2", "Papas fritas grande", "Refresco"]
    },
    {
        id: "#BB-242",
        total: "$75.50",
        customer: "Metro-Milial-Minja",
        paymentStatus: "pending",
        fulfillmentStatus: "processing",
        deliveryType: "Delivery",
        date: "9 de diciembre, 14:00",
        items: ["Hamburguesa BBQ", "Onion rings", "Batido de vainilla"]
    },
    {
        id: "#BB-241",
        total: "$37.50",
        customer: "Stanny Drinkwater",
        paymentStatus: "pending",
        fulfillmentStatus: "ready",
        deliveryType: "Local",
        date: "4 de diciembre, 12:36 p.m.",
        items: ["Hamburguesa Doble", "Papas fritas mediana"]
    },
    {
        id: "#BB-240",
        total: "$65.70",
        customer: "José Brandesky",
        paymentStatus: "cancelled",
        fulfillmentStatus: "processing",
        deliveryType: "Delivery",
        date: "1 de diciembre, 4:07 a.m.",
        items: ["Combo Familiar", "Postre brownie"]
    },
    {
        id: "#BB-239",
        total: "$96.30",
        customer: "Igor Brandham",
        paymentStatus: "paid",
        fulfillmentStatus: "delivered",
        deliveryType: "Local",
        date: "28 de noviembre, 19:28",
        items: ["Hamburguesa Vegana", "Ensalada César"]
    },
    {
        id: "#BB-238",
        total: "$46.00",
        customer: "Katerina Karenin",
        paymentStatus: "cancelled",
        fulfillmentStatus: "cancelled",
        deliveryType: "Local",
        date: "24 de noviembre, 10:26 p.m.",
        items: ["Hamburguesa Picante", "Refresco"]
    }
];

// Mapeo de estados CORREGIDO
const paymentStatusMap = {
    'pending': {class: 'badge-pending', text: 'Pendiente', icon: 'fa-clock'},
    'paid': {class: 'badge-paid', text: 'Pagado', icon: 'fa-check-circle'},
    'cancelled': {class: 'badge-cancelled', text: 'Cancelado', icon: 'fa-ban'}
};

const fulfillmentStatusMap = {
    'processing': {class: 'badge-processing', text: 'En preparación', icon: 'fa-utensils'},
    'ready': {class: 'badge-ready', text: 'Listo para entregar', icon: 'fa-box-open'},
    'delivered': {class: 'badge-delivered', text: 'Entregado', icon: 'fa-truck'},
    'cancelled': {class: 'badge-cancelled', text: 'Cancelado', icon: 'fa-times-circle'}
};

// Función para renderizar la tabla
function renderOrdersTable(filteredOrders = orders) {
    const tbody = document.getElementById('ordersTableBody');
    tbody.innerHTML = '';
    
    filteredOrders.forEach(order => {
        const paymentStatus = paymentStatusMap[order.paymentStatus] || paymentStatusMap['pending'];
        const fulfillmentStatus = fulfillmentStatusMap[order.fulfillmentStatus] || fulfillmentStatusMap['processing'];
        
        const row = document.createElement('tr');
        row.className = 'order-row';
        row.dataset.id = order.id;
        
        row.innerHTML = `
            <td>${order.id}</td>
            <td>${order.total}</td>
            <td>${order.customer}</td>
            <td>
                <span class="status-badge ${paymentStatus.class}">
                    <i class="fas ${paymentStatus.icon}"></i>
                    ${paymentStatus.text}
                </span>
            </td>
            <td>
                <span class="status-badge ${fulfillmentStatus.class}">
                    <i class="fas ${fulfillmentStatus.icon}"></i>
                    ${fulfillmentStatus.text}
                </span>
            </td>
            <td>${order.deliveryType}</td>
            <td>${order.date}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary change-status-btn" data-id="${order.id}">
                    <i class="fas fa-edit"></i> Cambiar
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Event listeners para botones de cambiar estado
    document.querySelectorAll('.change-status-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const orderId = this.dataset.id;
            const order = orders.find(o => o.id === orderId);
            
            if (order) {
                document.getElementById('modalOrderId').textContent = orderId;
                document.getElementById('modalPaymentStatus').value = order.paymentStatus;
                document.getElementById('modalFulfillmentStatus').value = order.fulfillmentStatus;
                
                const modal = new bootstrap.Modal(document.getElementById('statusModal'));
                modal.show();
            }
        });
    });
    
    // Event listener para ver detalles al hacer clic en la fila
    document.querySelectorAll('.order-row').forEach(row => {
        row.addEventListener('click', function() {
            const orderId = this.dataset.id;
            const order = orders.find(o => o.id === orderId);
            
            if (order) {
                alert(`Detalles del pedido ${orderId}:\n
                    Cliente: ${order.customer}\n
                    Total: ${order.total}\n
                    Productos:\n- ${order.items.join('\n- ')}`);
            }
        });
    });
}

// Función para aplicar filtros
function applyFilters() {
    const cliente = document.getElementById('filtroCliente').value.toLowerCase();
    const estadoPago = document.getElementById('filtroPago').value;
    const tipoEntrega = document.getElementById('filtroEntrega').value;

    const filtered = orders.filter(order => {
        const matchesCliente = order.customer.toLowerCase().includes(cliente);
        const matchesPago = estadoPago ? 
            (paymentStatusMap[order.paymentStatus]?.text === estadoPago) : true;
        const matchesEntrega = tipoEntrega ? 
            order.deliveryType.toLowerCase().includes(tipoEntrega.toLowerCase()) : true;
        
        return matchesCliente && matchesPago && matchesEntrega;
    });

    renderOrdersTable(filtered);
}

// Event listener para guardar cambios
document.getElementById('saveStatusBtn')?.addEventListener('click', function() {
    const orderId = document.getElementById('modalOrderId').textContent;
    const newPaymentStatus = document.getElementById('modalPaymentStatus').value;
    const newFulfillmentStatus = document.getElementById('modalFulfillmentStatus').value;
    
    const order = orders.find(o => o.id === orderId);
    if (order) {
        order.paymentStatus = newPaymentStatus;
        order.fulfillmentStatus = newFulfillmentStatus;
        renderOrdersTable();
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('statusModal'));
        modal.hide();
    }
});

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    // Verificar que Bootstrap esté cargado
    if (typeof bootstrap === 'undefined') {
        console.error("Bootstrap no está cargado");
        return;
    }

    // Renderizar tabla inicial
    renderOrdersTable();
    
    // Configurar event listeners para filtros
    document.getElementById('filtroCliente')?.addEventListener('input', applyFilters);
    document.getElementById('filtroPago')?.addEventListener('change', applyFilters);
    document.getElementById('filtroEntrega')?.addEventListener('change', applyFilters);
});