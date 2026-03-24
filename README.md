# 🍔 Brother's Burger — Sistema de Gestión

Sistema web de gestión de pedidos, cocina y facturación para el restaurante Brother's Burger, desarrollado con Django y PostgreSQL.

---

## 📋 Descripción

El sistema permite a los clientes realizar pedidos desde la web, al personal de cocina gestionar el estado de los pedidos en tiempo real, y al área administrativa controlar la facturación y los datos del negocio.

---

## 🏗️ Aplicaciones del proyecto

| App | Descripción |
|-----|-------------|
| `administrador` | Gestión de clientes, empleados, proveedores, productos, stock y compras |
| `pedidos` | Flujo de pedidos: panel de cliente, panel de cocina y panel de empleado |
| `facturacion` | Generación de facturas y timbrados |

---

## ⚙️ Requisitos

- Python 3.10+
- PostgreSQL 14+
- pip

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd brothers-burger
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
SECRET_KEY=tu_secret_key
DEBUG=True

DB_NAME=brothers_burger
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432
```

### 5. Configurar la base de datos

Crear la base de datos en PostgreSQL:

```sql
CREATE DATABASE brothers_burger;
```

### 6. Ejecutar migraciones

```bash
python manage.py migrate
```

### 7. Crear superusuario

```bash
python manage.py createsuperuser
```

### 8. Iniciar el servidor

```bash
python manage.py runserver
```

---

## 🗂️ Datos iniciales obligatorios

Antes de usar el sistema, cargar los siguientes datos desde el panel de administración en `/admin/`:

### ✅ Facturación
- Crear al menos un **Timbrado activo** en `/admin/facturacion/timbrado/`
  - Número de timbrado
  - RUC del emisor
  - Fecha de inicio y fin de vigencia
  - Marcar como **Activo**

> ⚠️ Sin un timbrado activo, el sistema no puede generar facturas.

### ✅ Ubicaciones
- Cargar **Ciudades** en `/admin/administrador/ciudad/`
- Cargar **Barrios** en `/admin/administrador/barrio/` y habilitarlos para delivery

### ✅ Productos
- Cargar **Categorías de productos** en `/admin/administrador/categoriaproducto/`
- Cargar **Productos** en `/admin/administrador/producto/`

---

## 🔄 Flujo principal del sistema

```
Cliente realiza pedido desde la web
        ↓
Cocina recibe el pedido (estado: Pendiente)
        ↓
Cocina lo toma (estado: En preparación)
        ↓
Cocina lo termina (estado: Listo)
        ↓
Empleado lo entrega al cliente (estado: Entregado)
        ↓
Sistema genera la factura automáticamente
        ↓
Pedido pasa a (estado: Facturado)
        ↓
Cliente puede ver su factura desde "Mis pedidos"
```

---

## 🌍 Configuración de zona horaria

El sistema está configurado para Paraguay. Verificar en `settings.py`:

```python
TIME_ZONE = 'America/Asuncion'
USE_TZ = True
```

---

## 📁 Estructura del proyecto

```
brothers_burger/
├── administrador/      # Clientes, empleados, productos, stock
├── pedidos/            # Pedidos, cocina, panel empleado
├── facturacion/        # Facturas y timbrados
├── media/              # Imágenes subidas (productos, etc.)
├── static/             # Archivos estáticos
├── templates/          # Templates base
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🔐 Roles del sistema

| Rol | Acceso |
|-----|--------|
| **Cliente** | Realizar pedidos, ver estado, ver factura |
| **Empleado de cocina** | Panel de cocina, avanzar estado de cocina |
| **Empleado** | Panel de empleado, marcar entregado |
| **Administrador** | Acceso completo al sistema y al admin de Django |

---

## 📌 Notas para el desarrollador

- Los pedidos del panel de cocina solo muestran los del **día actual** y excluyen los cancelados.
- La factura se genera **automáticamente** al marcar un pedido como Entregado, siempre que exista un timbrado activo.
- El campo `fecha` en el modelo `Pedido` es un `DateTimeField` con `auto_now_add=True`, se guarda en UTC pero se muestra en hora local de Paraguay.
