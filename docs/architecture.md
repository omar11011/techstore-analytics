# TechStore Analytics - Arquitectura del Sistema

> **Versión:** 1.0.0  
> **Última actualización:** 2025  
> **Arquitecto:** Equipo TechStore  
> **Estado:** Producción  

---

## 1. Visión General

**TechStore Analytics** es una plataforma de análisis de datos para una cadena de tiendas de tecnología que combina un backend API RESTful robusto con un dashboard interactivo de visualización. El sistema está diseñado con una **arquitectura en capas** (layered architecture) que separa claramente las responsabilidades entre presentación, lógica de negocio, acceso a datos y persistencia.

### Objetivos del Sistema

| Objetivo | Descripción |
|----------|-------------|
| **Análisis de ventas** | Visualización de tendencias, KPIs y métricas de rendimiento en tiempo real |
| **Gestión operativa** | CRUD completo para clientes, productos, pedidos, inventario y envíos |
| **Flexibilidad de despliegue** | Funcionamiento dual: PostgreSQL en producción o CSV demo para desarrollo |
| **Extensibilidad** | Arquitectura modular que facilita la adición de nuevas funcionalidades |
| **Rendimiento analítico** | Vistas SQL predefinidas e índices optimizados para consultas complejas |

### Principios de Diseño

- **Separación de responsabilidades (SoC):** Cada capa tiene una función bien definida
- **DRY (Don't Repeat Yourself):** Repositorio genérico base para operaciones CRUD comunes
- **Convention over Configuration:** Estructura de proyecto predecible y estandarizada
- **Graceful Degradation:** Fallback automático a modo CSV cuando PostgreSQL no está disponible
- **API-First:** El backend expone una API REST completa, consumible por cualquier cliente

---

## 2. Diagrama de Arquitectura

```mermaid
flowchart TB
    subgraph Cliente["🖥️ Capa de Cliente"]
        Browser["🌐 Navegador Web"]
        API_Client["📡 API Client<br/>(Postman, cURL, etc.)"]
    end

    subgraph Dashboard["📊 Dashboard Streamlit"]
        ST_App["streamlit_app.py<br/>Aplicación Principal"]
        Pages["Páginas del Dashboard"]
        Components["Componentes Reutilizables"]
        DataLoader["DataLoader<br/>(Modo Dual)"]
    end

    subgraph API_Layer["⚡ API Layer - FastAPI"]
        Main["main.py<br/>App Factory"]
        Routers["Routers API<br/>/api/v1/*"]
        Middleware["Middleware<br/>CORS + Timing"]
    end

    subgraph Service_Layer["🧠 Service Layer"]
        CustSvc["CustomerService"]
        ProdSvc["ProductService"]
        OrderSvc["OrderService"]
        AnalyticSvc["AnalyticsService"]
        OtherSvc["... otros servicios"]
    end

    subgraph Data_Layer["💾 Data Access Layer"]
        Repos["Repositorios<br/>(BaseRepository + especializados)"]
        Models["Modelos SQLAlchemy<br/>(ORM)"]
        Schemas["Schemas Pydantic<br/>(Validación)"]
    end

    subgraph Persistence["🗄️ Capa de Persistencia"]
        PG["PostgreSQL 16<br/>(Producción)"]
        CSV["Archivos CSV<br/>(Demo/Fallback)"]
        Views["Vistas SQL<br/>(6 vistas analíticas)"]
        Indexes["Índices<br/>(15 índices optimizados)"]
    end

    subgraph Infra["🐳 Infraestructura Docker"]
        DC["docker-compose.yml"]
        FastAPI_Container["Contenedor FastAPI<br/>:8000"]
        Streamlit_Container["Contenedor Streamlit<br/>:8501"]
        PG_Container["Contenedor PostgreSQL<br/>:5432"]
    end

    Browser --> ST_App
    API_Client --> Routers
    ST_App --> Pages
    Pages --> Components
    Pages --> DataLoader
    ST_App --> DataLoader

    DataLoader -->|PostgreSQL| PG
    DataLoader -->|CSV Fallback| CSV

    Main --> Routers
    Routers --> Middleware
    Routers --> CustSvc
    Routers --> ProdSvc
    Routers --> OrderSvc
    Routers --> AnalyticSvc
    Routers --> OtherSvc

    CustSvc --> Repos
    ProdSvc --> Repos
    OrderSvc --> Repos
    AnalyticSvc --> Repos

    Repos --> Models
    Routers --> Schemas

    Models --> PG
    PG --> Views
    PG --> Indexes

    DC --> FastAPI_Container
    DC --> Streamlit_Container
    DC --> PG_Container
```

---

## 3. Arquitectura en Capas

El sistema sigue un patrón de **arquitectura en capas** estricto donde cada capa solo se comunica con las capas adyacentes:

```mermaid
flowchart LR
    A["📡 API Layer<br/>(FastAPI Routers)"] --> B["🧠 Service Layer<br/>(Lógica de Negocio)"]
    B --> C["💾 Repository Layer<br/>(Acceso a Datos)"]
    C --> D["🏗️ Model Layer<br/>(ORM SQLAlchemy)"]
    D --> E["🗄️ Database<br/>(PostgreSQL)"]
```

### 3.1 API Layer (Capa de Presentación)

**Responsabilidad:** Recibir solicitudes HTTP, validar entradas con schemas Pydantic y devolver respuestas estructuradas.

| Componente | Archivo | Función |
|-----------|---------|---------|
| Application Factory | `app/main.py` | Configuración de la app FastAPI, CORS, middleware, routers |
| Customers Router | `app/api/customers.py` | Endpoints CRUD para `/api/v1/customers` |
| Products Router | `app/api/products.py` | Endpoints CRUD para `/api/v1/products` |
| Categories Router | `app/api/categories.py` | Endpoints CRUD para `/api/v1/categories` |
| Suppliers Router | `app/api/suppliers.py` | Endpoints CRUD para `/api/v1/suppliers` |
| Stores Router | `app/api/stores.py` | Endpoints CRUD para `/api/v1/stores` |
| Inventory Router | `app/api/inventory.py` | Endpoints CRUD para `/api/v1/inventory` |
| Orders Router | `app/api/orders.py` | Endpoints CRUD para `/api/v1/orders` |
| Payments Router | `app/api/payments.py` | Endpoints CRUD para `/api/v1/payments` |
| Shipments Router | `app/api/shipments.py` | Endpoints CRUD para `/api/v1/shipments` |
| Analytics Router | `app/api/analytics.py` | Endpoints analíticos para `/api/v1/analytics` |

**Características de la capa API:**
- Todos los routers registrados bajo el prefijo `/api/v1`
- Validación automática de entrada mediante schemas Pydantic
- Documentación automática con Swagger UI (`/docs`) y ReDoc (`/redoc`)
- Middleware CORS para acceso desde orígenes cruzados
- Middleware de timing con header `X-Process-Time`
- Manejo global de excepciones (`ValueError` → 400, `Exception` → 500)

### 3.2 Service Layer (Capa de Lógica de Negocio)

**Responsabilidad:** Encapsular la lógica de negocio, orquestar operaciones entre múltiples repositorios y aplicar reglas de validación.

| Servicio | Archivo | Función |
|---------|---------|---------|
| CustomerService | `app/services/customer_service.py` | Gestión de clientes y validaciones |
| ProductService | `app/services/product_service.py` | Gestión de productos, validación de márgenes |
| OrderService | `app/services/order_service.py` | Gestión de pedidos, cálculo de totales, workflow de estados |
| CategoryService | `app/services/category_service.py` | Gestión de categorías y jerarquías |
| SupplierService | `app/services/supplier_service.py` | Gestión de proveedores |
| StoreService | `app/services/store_service.py` | Gestión de tiendas |
| InventoryService | `app/services/inventory_service.py` | Gestión de inventario, alertas de stock |
| PaymentService | `app/services/payment_service.py` | Procesamiento de pagos, validación de métodos |
| ShipmentService | `app/services/shipment_service.py` | Seguimiento de envíos, workflow de estados |
| AnalyticsService | `app/services/analytics_service.py` | Consultas analíticas complejas, KPIs |

**Patrones utilizados:**
- **Inyección de dependencias:** Los servicios reciben la sesión de BD vía FastAPI `Depends()`
- **Principio de responsabilidad única:** Cada servicio gestiona una entidad del dominio
- **Orquestación:** El `OrderService` coordina la creación de pedidos, líneas y actualización de inventario

### 3.3 Repository Layer (Capa de Acceso a Datos)

**Responsabilidad:** Abstraer las operaciones de base de datos, proporcionar una interfaz genérica para CRUD y consultas especializadas.

| Componente | Archivo | Función |
|-----------|---------|---------|
| BaseRepository | `app/repositories/base_repository.py` | CRUD genérico parametrizable |
| CustomerRepository | `app/repositories/customer_repository.py` | Consultas específicas de clientes |
| ProductRepository | `app/repositories/product_repository.py` | Consultas específicas de productos |
| OrderRepository | `app/repositories/order_repository.py` | Consultas específicas de pedidos |
| AnalyticsRepo | `app/repositories/analytics_repo.py` | Consultas analíticas complejas |
| ... (otros) | `app/repositories/*.py` | Especializaciones por entidad |

**BaseRepository — Operaciones genéricas:**

```python
class BaseRepository(Generic[ModelType]):
    def create(db, **kwargs) -> ModelType       # INSERT
    def get_by_id(db, id) -> Optional[ModelType] # SELECT by PK
    def get_all(db, skip, limit) -> List         # SELECT with pagination
    def count(db) -> int                         # COUNT
    def update(db, id, **kwargs) -> Optional     # UPDATE by PK
    def delete(db, id) -> bool                   # DELETE by PK
```

**Ventajas del patrón:**
- Elimina duplicación de código CRUD entre repositorios
- Garantiza consistencia en las operaciones de acceso a datos
- Los repositorios especializados heredan las operaciones base y añaden consultas específicas

### 3.4 Model Layer (Capa de Modelos)

**Responsabilidad:** Definir la estructura de las tablas de base de datos y sus relaciones mediante el ORM SQLAlchemy.

**Ubicación:** `app/models/models.py`

**Modelos definidos:**

| Modelo | Tabla | Relaciones |
|--------|-------|-----------|
| `Customer` | `customers` | 1:N → `Order` |
| `Category` | `categories` | 1:N → `Product`, auto-ref → `Category` |
| `Supplier` | `suppliers` | 1:N → `Product` |
| `Product` | `products` | N:1 → `Category`, N:1 → `Supplier`, 1:N → `Inventory`, 1:N → `OrderItem` |
| `Store` | `stores` | 1:N → `Order`, 1:N → `Inventory` |
| `Inventory` | `inventory` | N:1 → `Product`, N:1 → `Store` |
| `Order` | `orders` | N:1 → `Customer`, N:1 → `Store`, 1:N → `OrderItem`, 1:1 → `Payment`, 1:1 → `Shipment` |
| `OrderItem` | `order_items` | N:1 → `Order`, N:1 → `Product` |
| `Payment` | `payments` | 1:1 → `Order` |
| `Shipment` | `shipments` | 1:1 → `Order` |

**Características del ORM:**
- Estrategia de carga `selectin` (eager loading) para evitar el problema N+1
- Cascade `all, delete-orphan` con `passive_deletes=True` para relaciones dependientes
- Mixin `TimestampMixin` para columnas `created_at`/`updated_at` reutilizables
- Propiedad `__repr__` en cada modelo para debugging legible

### 3.5 Database Layer (Capa de Persistencia)

**Responsabilidad:** Gestión de conexiones, sesiones y configuración del motor de base de datos.

**Ubicación:** `app/database/config.py`

**Configuración del engine:**

| Parámetro | Valor | Propósito |
|-----------|-------|-----------|
| `pool_size` | 10 | Conexiones permanentes en el pool |
| `max_overflow` | 20 | Conexiones adicionales permitidas |
| `pool_pre_ping` | True | Validar conexiones antes de usarlas |
| `echo` | False | No logear SQL en producción |

**Gestión de sesiones:**
- Patrón Unit of Work: sesión por request con `get_db()` como dependencia FastAPI
- Rollback automático en caso de excepción
- Cierre garantizado de sesión en el bloque `finally`

---

## 4. Estructura de la API REST

### 4.1 Endpoints por Entidad

Todos los endpoints están bajo el prefijo `/api/v1`:

```
/api/v1/customers          → CRUD de clientes
/api/v1/products           → CRUD de productos
/api/v1/categories         → CRUD de categorías
/api/v1/suppliers          → CRUD de proveedores
/api/v1/stores             → CRUD de tiendas
/api/v1/inventory          → CRUD de inventario
/api/v1/orders             → CRUD de pedidos
/api/v1/payments           → CRUD de pagos
/api/v1/shipments          → CRUD de envíos
/api/v1/analytics          → Consultas analíticas y KPIs
```

### 4.2 Patrón de Endpoints CRUD

Cada entidad sigue el mismo patrón RESTful:

| Método | Endpoint | Descripción | Código de respuesta |
|--------|----------|-------------|-------------------|
| `GET` | `/api/v1/{entity}` | Listar con paginación (`skip`, `limit`) | 200 |
| `GET` | `/api/v1/{entity}/{id}` | Obtener por ID | 200 / 404 |
| `POST` | `/api/v1/{entity}` | Crear nuevo registro | 201 / 400 |
| `PATCH` | `/api/v1/{entity}/{id}` | Actualización parcial | 200 / 404 |
| `DELETE` | `/api/v1/{entity}/{id}` | Eliminar registro | 204 / 404 |

### 4.3 Schemas de Validación (Pydantic)

Para cada entidad se definen tres tipos de schema:

| Tipo | Propósito | Campos |
|------|-----------|--------|
| **CreateSchema** | Validar datos de entrada (POST) | Todos los campos requeridos |
| **UpdateSchema** | Actualización parcial (PATCH) | Todos los campos opcionales |
| **ResponseSchema** | Dar forma a la respuesta (GET) | Incluye `id`, `created_at`, relaciones |

**Configuración Pydantic v2:**

```python
model_config = ConfigDict(from_attributes=True)  # Conversión ORM → dict automática
```

### 4.4 Endpoints Analíticos

El router de analytics expone endpoints especializados para el dashboard:

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/v1/analytics/dashboard-summary` | KPIs principales (ventas totales, órdenes, clientes, ticket promedio, margen) |
| `GET /api/v1/analytics/monthly-sales` | Tendencia de ventas mensuales |
| `GET /api/v1/analytics/top-products` | Productos más vendidos por ingreso |
| `GET /api/v1/analytics/top-customers` | Clientes con mayor gasto |
| `GET /api/v1/analytics/category-sales` | Ventas por categoría |
| `GET /api/v1/analytics/store-performance` | Rendimiento por tienda |
| `GET /api/v1/analytics/inventory-status` | Estado del inventario con alertas |

### 4.5 Paginación

Se implementa un wrapper genérico de paginación:

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]         # Elementos de la página actual
    total: int            # Total de registros
    page: int             # Página actual
    page_size: int        # Tamaño de página
    total_pages: int      # Total de páginas
```

---

## 5. Arquitectura del Dashboard

### 5.1 Componentes

```mermaid
flowchart TB
    subgraph Streamlit_App["📊 Streamlit Application"]
        Main["streamlit_app.py<br/>Navegación + Filtros"]
        
        subgraph Pages["📄 Páginas"]
            Exec["📊 Resumen Ejecutivo"]
            Sales["💰 Ventas"]
            Cust["👥 Clientes"]
            Prod["🛍️ Productos"]
            Inv["📦 Inventario"]
            SQL["🗄️ SQL Showcase"]
        end

        subgraph Components["🧩 Componentes"]
            Charts["charts.py<br/>Gráficos Plotly"]
            KPIs["kpi_cards.py<br/>Tarjetas KPI"]
        end

        DL["DataLoader<br/>Modo Dual PG/CSV"]
    end

    Main --> Pages
    Pages --> Components
    Pages --> DL
    DL -->|PostgreSQL| DB["🗄️ PostgreSQL"]
    DL -->|CSV Fallback| CSVs["📁 data/demo/"]
```

### 5.2 Páginas del Dashboard

| Página | Archivo | Funcionalidad |
|--------|---------|---------------|
| **Resumen Ejecutivo** | `dashboard/pages/executive_summary.py` | KPIs generales, ventas totales, tendencias, top productos/clientes |
| **Ventas** | `dashboard/pages/sales.py` | Análisis detallado de ventas, tendencia mensual, distribución por categoría |
| **Clientes** | `dashboard/pages/customers.py` | Análisis de clientes, segmentación, top compradores, distribución geográfica |
| **Productos** | `dashboard/pages/products.py` | Catálogo de productos, rentabilidad, rendimiento por categoría |
| **Inventario** | `dashboard/pages/inventory.py` | Estado de stock, alertas de reorden, distribución por tienda |
| **SQL Showcase** | `dashboard/pages/sql_showcase.py` | Demostración de consultas SQL avanzadas, vistas y optimizaciones |

### 5.3 Sistema de Filtros

El dashboard implementa filtros globales en el sidebar que afectan a todas las páginas:

| Filtro | Tipo | Valores |
|--------|------|---------|
| **Rango de Fechas** | `st.date_input` | Rango dinámico basado en datos de pedidos |
| **Categoría** | `st.selectbox` | Lista de categorías + "Todas" |
| **Sucursal** | `st.selectbox` | Lista de tiendas + "Todas" |

### 5.4 Componentes Reutilizables

| Componente | Archivo | Función |
|-----------|---------|---------|
| `charts.py` | `dashboard/components/charts.py` | Funciones helper para crear gráficos Plotly con estilo consistente |
| `kpi_cards.py` | `dashboard/components/kpi_cards.py` | Tarjetas de métricas con formato y deltas |

### 5.5 Caché de Datos

Se utiliza `@st.cache_data` con TTL de 600 segundos (10 minutos) para todas las consultas de datos:

```python
@st.cache_data(ttl=600, show_spinner=False)
def get_orders(_self) -> pd.DataFrame:
    ...
```

El DataLoader se instancia como recurso cacheado con `@st.cache_resource`:

```python
@st.cache_resource
def get_loader() -> DataLoader:
    return DataLoader()
```

---

## 6. Diseño de Modo Dual (PostgreSQL / CSV)

Una de las características distintivas del sistema es su capacidad de funcionar en **dos modos** sin cambios en el código de presentación:

```mermaid
flowchart LR
    DL["DataLoader"] -->|¿DATABASE_URL disponible?| Check{Check}
    Check -->|Sí| PG["🟢 Modo PostgreSQL<br/>Consultas SQL directas"]
    Check -->|No| CSV["🔴 Modo CSV Demo<br/>Archivos locales"]
    
    PG --> Data1["DataFrames<br/>con datos de BD"]
    CSV --> Data2["DataFrames<br/>con datos CSV"]
    
    Data1 --> Dashboard["📊 Dashboard<br/>(Transparente al modo)"]
    Data2 --> Dashboard
```

### 6.1 Mecanismo de Selección Automática

El `DataLoader` implementa la lógica de selección automática en su constructor:

```
1. Intentar obtener DATABASE_URL de st.secrets["database"]
2. Si no existe, intentar obtenerla de la variable de entorno DATABASE_URL
3. Si se encuentra, intentar conectar a PostgreSQL (SELECT 1)
4. Si la conexión falla, activar modo demo (CSV)
5. Si no hay URL, activar modo demo directamente
```

### 6.2 Normalización de Columnas

En modo CSV, las columnas se normalizan para mantener compatibilidad con el modo PostgreSQL:

| Columna CSV | Columna Normalizada | Motivo |
|-------------|-------------------|--------|
| `id` | `{entity}_id` (ej: `customer_id`) | Consistencia con esquema SQL |
| `price` | `unit_price` | Coincidir con nombre SQL |
| `cost` | `cost_price` | Coincidir con nombre SQL |
| `category` | `category_name` | Coincidir con JOIN de SQL |
| — | `line_total` | Se calcula si no existe |
| — | `status` (inventory) | Se calcula a partir de `stock_quantity` y `reorder_level` |

### 6.3 Indicadores de Modo

El dashboard muestra indicadores visuales del modo activo:

| Modo | Indicador | Banner |
|------|-----------|--------|
| **PostgreSQL** | 🟢 **Modo:** PostgreSQL, 🗄️ **Fuente:** Base de datos activa | Ninguno |
| **CSV Demo** | 🔴 **Modo:** CSV Demo, 📁 **Fuente:** `data/demo/` | ⚠️ Banner amarillo con aviso |

### 6.4 Datos Demo

Los archivos CSV de demostración se almacenan en `data/demo/`:

| Archivo | Contenido |
|---------|-----------|
| `customers.csv` | Datos de clientes de ejemplo |
| `products.csv` | Catálogo de productos de ejemplo |
| `categories.csv` | Categorías de productos |
| `orders.csv` | Pedidos de ejemplo |
| `order_items.csv` | Líneas de pedido de ejemplo |
| `stores.csv` | Tiendas de ejemplo |
| `monthly_sales.csv` | Agregación mensual pre-calculada |
| `top_products.csv` | Top productos por ingreso |
| `top_customers.csv` | Top clientes por gasto |
| `category_sales.csv` | Ventas por categoría |
| `inventory_status.csv` | Estado de inventario |
| `store_performance.csv` | Rendimiento por tienda |

---

## 7. Arquitectura Docker

### 7.1 Servicios

El despliegue se realiza mediante Docker Compose con tres servicios:

```mermaid
flowchart TB
    subgraph Docker_Compose["🐳 docker-compose.yml"]
        subgraph FastAPI_Service["⚡ FastAPI Service"]
            FA_Container["Container: fastapi<br/>Port: 8000"]
            FA_Vol["Volume: ./app:/app/app<br/>(Hot Reload)"]
        end

        subgraph Streamlit_Service["📊 Streamlit Service"]
            ST_Container["Container: streamlit<br/>Port: 8501"]
        end

        subgraph PostgreSQL_Service["🗄️ PostgreSQL Service"]
            PG_Container["Container: postgres<br/>Port: 5432"]
            PG_Vol["Volume: postgres_data<br/>(Persistencia)"]
            PG_Health["Healthcheck:<br/>pg_isready -U techstore"]
        end
    end

    FA_Container --> PG_Container
    ST_Container --> PG_Container
    FA_Vol --> FA_Container
    PG_Vol --> PG_Container
```

### 7.2 Configuración de Servicios

| Servicio | Imagen | Puerto | Dependencias | Comando |
|----------|--------|--------|-------------|---------|
| **postgres** | `postgres:16-alpine` | 5432 | — | (default) |
| **fastapi** | Custom Dockerfile | 8000 | postgres (healthy) | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| **streamlit** | Custom Dockerfile | 8501 | postgres (healthy) | `streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0` |

### 7.3 Dockerfile

El Dockerfile es **multifunción** — sirve tanto para FastAPI como para Streamlit:

```dockerfile
FROM python:3.12-slim
WORKDIR /app

# Dependencias del sistema (gcc para compilar psycopg2, libpq-dev para PostgreSQL)
RUN apt-get update && apt-get install -y gcc libpq-dev

# Instalación de dependencias Python
COPY requirements.txt .
COPY requirements-dashboard.txt .
RUN pip install -r requirements.txt
RUN pip install -r requirements-dashboard.txt

# Código de la aplicación
COPY . .

# Puertos expuestos (elegido en runtime por docker-compose)
EXPOSE 8000 8501

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.4 Healthcheck de PostgreSQL

El servicio PostgreSQL incluye un healthcheck que los otros servicios esperan antes de iniciar:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U techstore"]
  interval: 5s
  timeout: 5s
  retries: 5
```

### 7.5 Variables de Entorno

| Variable | Servicio | Valor por defecto | Propósito |
|----------|----------|-------------------|-----------|
| `DATABASE_URL` | fastapi, streamlit | `postgresql://techstore:techstore@postgres:5432/techstore` | URL de conexión a PostgreSQL |
| `POSTGRES_DB` | postgres | `techstore` | Nombre de la base de datos |
| `POSTGRES_USER` | postgres | `techstore` | Usuario de la base de datos |
| `POSTGRES_PASSWORD` | postgres | `techstore` | Contraseña de la base de datos |

### 7.6 Volúmenes

| Volumen | Montaje | Propósito |
|---------|---------|-----------|
| `postgres_data` | `/var/lib/postgresql/data` | Persistencia de datos de PostgreSQL |
| `./app:/app/app` | (bind mount) | Hot reload del código FastAPI durante desarrollo |

---

## 8. Estructura del Proyecto

```
techstore/
├── app/                          # Backend FastAPI
│   ├── __init__.py
│   ├── main.py                   # Application factory, CORS, routers
│   ├── api/                      # Capa API (Routers)
│   │   ├── __init__.py
│   │   ├── analytics.py          # Endpoints analíticos
│   │   ├── categories.py         # CRUD categorías
│   │   ├── customers.py          # CRUD clientes
│   │   ├── inventory.py          # CRUD inventario
│   │   ├── orders.py             # CRUD pedidos
│   │   ├── payments.py           # CRUD pagos
│   │   ├── products.py           # CRUD productos
│   │   ├── shipments.py          # CRUD envíos
│   │   ├── stores.py             # CRUD tiendas
│   │   └── suppliers.py          # CRUD proveedores
│   ├── database/                 # Configuración de BD
│   │   ├── __init__.py
│   │   └── config.py             # Engine, Session, Base
│   ├── models/                   # Modelos ORM
│   │   ├── __init__.py
│   │   └── models.py             # 10 modelos SQLAlchemy
│   ├── repositories/             # Capa de acceso a datos
│   │   ├── __init__.py
│   │   ├── base_repository.py    # CRUD genérico
│   │   ├── customer_repository.py
│   │   ├── product_repository.py
│   │   ├── order_repository.py
│   │   ├── analytics_repo.py
│   │   └── ... (otros repositorios)
│   ├── schemas/                  # Schemas Pydantic
│   │   ├── __init__.py
│   │   └── schemas.py            # Validación y serialización
│   ├── services/                 # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── analytics_service.py
│   │   ├── customer_service.py
│   │   ├── order_service.py
│   │   ├── product_service.py
│   │   └── ... (otros servicios)
│   └── utils/                    # Utilidades
│       └── __init__.py
├── dashboard/                    # Dashboard Streamlit
│   ├── __init__.py
│   ├── data_loader.py            # DataLoader modo dual
│   ├── components/               # Componentes reutilizables
│   │   ├── __init__.py
│   │   ├── charts.py             # Helpers de gráficos Plotly
│   │   └── kpi_cards.py          # Tarjetas KPI
│   └── pages/                    # Páginas del dashboard
│       ├── __init__.py
│       ├── executive_summary.py
│       ├── sales.py
│       ├── customers.py
│       ├── products.py
│       ├── inventory.py
│       └── sql_showcase.py
├── sql/                          # Scripts SQL
│   ├── schema.sql                # DDL completo (10 tablas)
│   ├── views.sql                 # 6 vistas analíticas
│   ├── indexes.sql               # 15 índices optimizados
│   └── showcase_queries.sql      # Consultas de demostración
├── scripts/                      # Scripts de utilidad
│   ├── generate_demo_csv.py      # Generador de datos CSV demo
│   └── seed_database.py          # Poblador de base de datos
├── tests/                        # Tests automatizados
│   ├── __init__.py
│   ├── conftest.py               # Fixtures compartidas
│   ├── test_database.py
│   ├── test_customers.py
│   ├── test_products.py
│   ├── test_orders.py
│   └── test_analytics.py
├── alembic/                      # Migraciones
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── alembic.ini                   # Configuración de Alembic
├── data/                         # Datos
│   └── demo/                     # CSVs para modo demo
├── docs/                         # Documentación
│   ├── erd.md                    # Diagrama Entidad-Relación
│   └── architecture.md           # Este documento
├── streamlit_app.py              # Entry point del dashboard
├── docker-compose.yml            # Orquestación de contenedores
├── Dockerfile                    # Imagen Docker
├── requirements.txt              # Dependencias del backend
└── requirements-dashboard.txt    # Dependencias del dashboard
```

---

## 9. Stack Tecnológico

### 9.1 Backend

| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| **Python** | 3.12 | Lenguaje de programación principal |
| **FastAPI** | — | Framework web asíncrono de alto rendimiento |
| **Uvicorn** | — | Servidor ASGI para FastAPI |
| **SQLAlchemy** | — | ORM y toolkit de base de datos |
| **Alembic** | — | Herramienta de migración de base de datos |
| **Pydantic** | v2 | Validación de datos y serialización |
| **psycopg2** | — | Adaptador PostgreSQL para Python |

### 9.2 Dashboard

| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| **Streamlit** | — | Framework de dashboard interactivo |
| **Plotly** | — | Biblioteca de visualización interactiva |
| **Pandas** | — | Manipulación y análisis de datos |

### 9.3 Base de Datos

| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| **PostgreSQL** | 16 | Sistema de gestión de base de datos relacional |
| **Alpine Linux** | — | Imagen base ligera para Docker |

### 9.4 Infraestructura

| Tecnología | Propósito |
|-----------|-----------|
| **Docker** | Containerización de servicios |
| **Docker Compose** | Orquestación multi-contenedor |

---

## 10. Seguridad

### 10.1 Medidas Implementadas

| Medida | Implementación | Detalle |
|--------|---------------|---------|
| **Validación de entrada** | Pydantic schemas | Todos los datos de entrada son validados contra schemas estrictos |
| **Protección contra SQL Injection** | SQLAlchemy ORM | Uso de ORM con parámetros vinculados en todas las consultas |
| **CORS** | FastAPI middleware | Configuración de orígenes permitidos (actualmente `*` para desarrollo) |
| **Constraints de BD** | CHECK constraints | Validación de dominio en la base de datos (estados, rangos, formatos) |
| **Manejo de errores** | Exception handlers | Sin exposición de detalles internos en respuestas de error 500 |
| **Soft delete** | Banderas `is_active` | Eliminación lógica en lugar de física para datos críticos |
| **Pool de conexiones** | SQLAlchemy pool | Gestión eficiente y segura de conexiones de base de datos |

### 10.2 Consideraciones para Producción

Las siguientes medidas deben implementarse antes del despliegue en producción:

| Área | Recomendación | Prioridad |
|------|--------------|-----------|
| **Autenticación** | Implementar JWT/OAuth2 con FastAPI security | 🔴 Alta |
| **Autorización** | Control de acceso basado en roles (RBAC) | 🔴 Alta |
| **CORS** | Restringir orígenes a dominios específicos | 🔴 Alta |
| **Contraseñas** | Variables de entorno en secrets manager, no en docker-compose | 🔴 Alta |
| **HTTPS** | Certificado SSL/TLS con reverse proxy (nginx/caddy) | 🟡 Media |
| **Rate Limiting** | Protección contra abuso de API | 🟡 Media |
| **Logging** | Implementar logging estructurado con rotación | 🟡 Media |
| **Backup** | Estrategia automatizada de respaldo de PostgreSQL | 🟡 Media |
| **Auditoría** | Log de operaciones sensibles (CREATES, UPDATES, DELETES) | 🟢 Baja |
| **Encriptación** | Encriptación de datos sensibles en reposo (PII) | 🟢 Baja |

---

## 11. Escalabilidad

### 11.1 Escalabilidad Vertical

El sistema está preparado para escalar verticalmente mediante:

| Recurso | Parámetro actual | Ajuste recomendado |
|---------|-----------------|-------------------|
| Pool de conexiones BD | `pool_size=10`, `max_overflow=20` | Incrementar según carga: `pool_size=20`, `max_overflow=40` |
| Workers Uvicorn | 1 (single process) | `uvicorn --workers 4` para aprovechar múltiples núcleos |
| Memoria PostgreSQL | Default Alpine | Ajustar `shared_buffers`, `work_mem`, `effective_cache_size` |
| Cache Streamlit | `ttl=600` (10 min) | Ajustar según frecuencia de actualización requerida |

### 11.2 Escalabilidad Horizontal

Para escalar horizontalmente se recomienda:

| Componente | Estrategia | Implementación |
|-----------|-----------|---------------|
| **API FastAPI** | Múltiples réplicas detrás de un load balancer | Docker Compose scale o Kubernetes HPA |
| **PostgreSQL** | Read replicas para consultas analíticas | Streaming replication con pg_stat_statements |
| **Dashboard** | Múltiples instancias con sticky sessions | Streamlit Cloud o部署 en Kubernetes |
| **Cache** | Redis como capa de caché compartida | Reemplazar `st.cache_data` por Redis con TTL |
| **Colas** | Celery + Redis para tareas asíncronas | Reportes pesados, generación de CSV, notificaciones |

### 11.3 Cuellos de Botella Identificados

| Cuello | Impacto | Mitigación |
|--------|---------|-----------|
| **Consultas analíticas pesadas** | Latencia en dashboard | Vistas materializadas + cache |
| **Escrituras concurrentes en inventario** | Contención de locks | Optimistic locking o advisory locks |
| **Conexiones de BD por worker** | Agotamiento del pool | PgBouncer como connection pooler externo |
| **Tamaño de datos CSV demo** | Carga lenta en desarrollo | Comprimir CSVs o usar Parquet |

### 11.4 Estrategia de Caché Recomendada

```mermaid
flowchart LR
    Request["📥 Request"] --> Cache{¿En caché?}
    Cache -->|Sí| Response["📤 Response<br/>(from cache)"]
    Cache -->|No| DB["🗄️ PostgreSQL"]
    DB --> SetCache["💾 Set Cache<br/>(TTL: 10 min)"]
    SetCache --> Response
```

| Capa | Tecnología | TTL | Invalidación |
|------|-----------|-----|-------------|
| **Aplicación** | `st.cache_data` | 600s | Automática por TTL |
| **Base de datos** | Vistas materializadas | Manual | `REFRESH MATERIALIZED VIEW` |
| **Distribuida** (futuro) | Redis | 300s | Event-driven via PostgreSQL LISTEN/NOTIFY |

---

## 12. Monitoreo y Observabilidad

### 12.1 Logging

El sistema utiliza el módulo `logging` estándar de Python con configuración centralizada:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
```

| Logger | Propósito |
|--------|-----------|
| `techstore` | Logger raíz de la aplicación |
| `app.database` | Eventos de conexión y sesiones |
| `app.repositories` | Operaciones CRUD (nivel DEBUG) |
| `app.services` | Eventos de lógica de negocio |

### 12.2 Health Check

El endpoint `/health` proporciona verificación de estado del servicio:

```json
{
    "status": "healthy",
    "service": "TechStore Analytics API",
    "version": "1.0.0"
}
```

### 12.3 Métricas de Rendimiento

El middleware de timing añade el header `X-Process-Time` a cada respuesta, permitiendo medir la latencia de procesamiento del servidor:

```
X-Process-Time: 0.0234
```

---

## 13. Flujo de Datos Principal

### 13.1 Creación de un Pedido

```mermaid
sequenceDiagram
    participant Client as Cliente API
    participant API as FastAPI Router
    participant Schema as Pydantic Schema
    participant Service as OrderService
    participant Repo as OrderRepository
    participant DB as PostgreSQL

    Client->>API: POST /api/v1/orders
    API->>Schema: Validar OrderCreate
    Schema-->>API: Datos validados
    API->>Service: create_order(data)
    Service->>Repo: create(order_data)
    Repo->>DB: INSERT INTO orders
    DB-->>Repo: order_id=42
    Service->>Repo: create_items(items)
    Repo->>DB: INSERT INTO order_items
    DB-->>Repo: items created
    Service-->>API: OrderResponse
    API-->>Client: 201 Created
```

### 13.2 Consulta del Dashboard

```mermaid
sequenceDiagram
    participant User as Usuario
    participant ST as Streamlit
    participant DL as DataLoader
    participant PG as PostgreSQL
    participant CSV as Archivos CSV

    User->>ST: Accede al Dashboard
    ST->>DL: get_loader()
    DL->>DL: Verificar DATABASE_URL
    alt PostgreSQL disponible
        DL->>PG: SELECT 1 (health check)
        PG-->>DL: OK
        DL-->>ST: Modo PostgreSQL
    else PostgreSQL no disponible
        DL-->>ST: Modo CSV Demo
    end
    
    User->>ST: Selecciona "Ventas"
    ST->>DL: get_monthly_sales()
    alt Modo PostgreSQL
        DL->>PG: SELECT ... FROM monthly_sales_summary
        PG-->>DL: DataFrame
    else Modo CSV
        DL->>CSV: pd.read_csv("monthly_sales.csv")
        CSV-->>DL: DataFrame
    end
    DL-->>ST: DataFrame con ventas
    ST->>User: Gráficos y métricas
```

---

## 14. Convenciones y Estándares

### 14.1 Estilo de Código

| Convención | Estándar |
|-----------|---------|
| **Lenguaje** | Python 3.12+ |
| **Tipado** | Type hints en todas las funciones |
| **Docstrings** | Formato Google/NumPy |
| **Imports** | Orden: stdlib → third-party → local |
| **Naming** | `snake_case` para funciones/variables, `PascalCase` para clases |
| **Line length** | 88 caracteres (Black compatible) |
| **Strings** | Comillas dobles (`"`) |

### 14.2 Convenciones de API

| Convención | Implementación |
|-----------|---------------|
| **Versionado** | Prefijo `/api/v1` |
| **RESTful** | Recursos como sustantivos, verbos HTTP semánticos |
| **Paginación** | Parámetros `skip` y `limit` |
| **Errores** | Formato `{"detail": "mensaje"}` |
| **Códigos de estado** | 200, 201, 400, 404, 500 |
| **Content-Type** | `application/json` |

### 14.3 Convenciones de Base de Datos

| Convención | Implementación |
|-----------|---------------|
| **Nombres de tabla** | Plural, `snake_case` (ej: `order_items`) |
| **Claves primarias** | `{tabla_singular}_id` (ej: `customer_id`) |
| **Claves foráneas** | Mismo nombre que PK referenciada |
| **Timestamps** | `created_at`, `updated_at` con `DEFAULT CURRENT_TIMESTAMP` |
| **Soft delete** | Columna `is_active BOOLEAN DEFAULT TRUE` |
| **Comentarios** | `COMMENT ON` en tablas, columnas e índices |

---

> **Documento generado para el proyecto TechStore Analytics**  
> **Stack tecnológico:** FastAPI + SQLAlchemy + PostgreSQL + Streamlit + Docker  
> **Licencia:** Proyecto de portafolio
