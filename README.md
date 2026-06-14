<div align="center">

# TechStore Analytics Backend

**Sistema de análisis y backend profesional para tienda de tecnología**

_Demostración de dominio en SQL, FastAPI, PostgreSQL, dashboards analíticos y arquitectura profesional_

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## Descripcion

**TechStore Analytics Backend** es un sistema completo de analisis de datos y API REST para una tienda de tecnologia, disenado como proyecto de portafolio para demostrar competencias profesionales en desarrollo backend, bases de datos relacionales y visualizacion de datos.

El proyecto implementa una arquitectura por capas (**layered architecture**) con separacion clara de responsabilidades: desde los modelos ORM hasta la capa de presentacion, pasando por repositorios, servicios y endpoints REST. Incluye un **dashboard analitico interactivo** construido con Streamlit y Plotly que permite explorar KPIs de negocio, tendencias de ventas, comportamiento de clientes y estado de inventario en tiempo real.

La base de datos PostgreSQL contiene **10 tablas normalizadas** con restricciones de integridad referencial, CHECK constraints, indices optimizados y vistas. El **SQL Showcase** presenta 20 consultas avanzadas que demuestran dominio de CTEs, Window Functions, subconsultas correlacionadas y funciones de agregacion complejas.

La API REST construida con FastAPI ofrece **50+ endpoints** con documentacion automatica (Swagger UI / ReDoc), validacion de datos con Pydantic v2, paginacion, filtros dinamicos y manejo robusto de errores. Todo el proyecto esta contenerizado con Docker y Docker Compose para facilitar su despliegue y ejecucion.

---

## Objetivo

Este proyecto resuelve un problema real: **la necesidad de centralizar y visualizar los datos operativos de una tienda de tecnologia** para tomar decisiones de negocio informadas. Al mismo tiempo, demuestra de forma practica las siguientes competencias:

- **SQL avanzado**: CTEs recursivas, Window Functions (`RANK`, `LAG`, `SUM OVER`), subconsultas correlacionadas, `CASE WHEN` complejos, `GENERATED COLUMNS`, y consultas analiticas de negocio.
- **Diseno de base de datos relacional**: 10 tablas normalizadas con claves foraneas, restricciones CHECK, indices compuestos y relaciones 1:1, 1:N y M:N.
- **Backend profesional con FastAPI**: API REST completa con validacion, documentacion automatica, manejo de errores, middleware de CORS y timing, y patron Repository.
- **Dashboard analitico**: Visualizacion interactiva con Streamlit y Plotly, modo dual (PostgreSQL / CSV demo), filtros dinamicos y KPIs de negocio.
- **Arquitectura escalable**: Separacion por capas que permite modificar cualquier componente sin afectar los demas, facilitando testing y mantenimiento.

---

## Stack Tecnologico

| Tecnologia | Version | Proposito |
|---|---|---|
| **Python** | 3.12 | Lenguaje principal del proyecto |
| **FastAPI** | 0.115 | Framework web para la API REST |
| **PostgreSQL** | 16 | Base de datos relacional principal |
| **SQLAlchemy** | 2.0 | ORM para mapeo objeto-relacional |
| **Alembic** | 1.13 | Herramienta de migraciones de base de datos |
| **Pydantic** | 2.9 | Validacion de datos y serializacion |
| **Streamlit** | 1.38 | Framework para el dashboard analitico |
| **Plotly** | 5.24 | Libreria de visualizacion interactiva |
| **Pandas** | 2.2 | Manipulacion y analisis de datos |
| **Faker** | 28.4 | Generacion de datos de prueba realistas |
| **Pytest** | 8.3 | Framework de testing |
| **Docker** | — | Contenerizacion de servicios |
| **Docker Compose** | 3.8 | Orquestacion multi-contenedor |
| **Uvicorn** | 0.30 | Servidor ASGI para FastAPI |
| **psycopg2** | 2.9 | Driver PostgreSQL para Python |

---

## Arquitectura

El proyecto sigue una **arquitectura por capas** (Layered Architecture) con separacion estricta de responsabilidades. Cada capa solo se comunica con la capa inmediatamente inferior, lo que garantiza bajo acoplamiento y alta cohesion.

```mermaid
graph TD
    subgraph Presentation Layer
        A[Streamlit Dashboard]
        B[Swagger UI / ReDoc]
    end

    subgraph API Layer
        C[FastAPI REST Endpoints]
    end

    subgraph Service Layer
        D[Business Logic]
    end

    subgraph Repository Layer
        E[Data Access]
    end

    subgraph Model Layer
        F[SQLAlchemy ORM Models]
    end

    subgraph Database Layer
        G[(PostgreSQL 16)]
    end

    A --> C
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G

    style A fill:#FF4B4B,color:#fff
    style B fill:#009688,color:#fff
    style C fill:#009688,color:#fff
    style D fill:#3B82F6,color:#fff
    style E fill:#8B5CF6,color:#fff
    style F fill:#F59E0B,color:#fff
    style G fill:#336791,color:#fff
```

### Descripcion de las capas

| Capa | Componente | Responsabilidad |
|---|---|---|
| **Presentation** | `streamlit_app.py`, `dashboard/` | Interfaz de usuario, graficos, filtros, KPIs |
| **API** | `app/api/` | Endpoints REST, validacion de entrada, serializacion de respuesta |
| **Service** | `app/services/` | Logica de negocio, orquestacion, calculos derivados |
| **Repository** | `app/repositories/` | Acceso a datos, consultas ORM, operaciones CRUD genericas |
| **Model** | `app/models/` | Definicion de tablas, columnas, relaciones y constraints |
| **Database** | PostgreSQL | Persistencia, integridad referencial, indices, vistas |

---

## Modelo de Datos

La base de datos consta de **10 tablas** con relaciones normalizadas que modelan completamente la operacion de una tienda de tecnologia: desde el catalogo de productos y proveedores hasta las ordenes, pagos y envios.

```mermaid
erDiagram
    customers {
        int id PK
        varchar first_name
        varchar last_name
        varchar email UK
        varchar phone
        varchar city
        varchar country
        timestamp created_at
    }

    categories {
        int id PK
        varchar name UK
        text description
    }

    suppliers {
        int id PK
        varchar company_name
        varchar contact_name
        varchar email UK
        varchar phone
        varchar country
    }

    products {
        int id PK
        varchar sku UK
        varchar name
        text description
        numeric price
        numeric cost
        int category_id FK
        int supplier_id FK
        timestamp created_at
    }

    stores {
        int id PK
        varchar name
        varchar city
        varchar country
    }

    inventory {
        int id PK
        int store_id FK
        int product_id FK
        int stock_quantity
        timestamp updated_at
    }

    orders {
        int id PK
        int customer_id FK
        int store_id FK
        timestamp order_date
        numeric total_amount
        varchar status
    }

    order_items {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        numeric unit_price
        numeric discount
    }

    payments {
        int id PK
        int order_id FK
        varchar payment_method
        varchar payment_status
        timestamp payment_date
        numeric amount
    }

    shipments {
        int id PK
        int order_id FK
        varchar shipment_status
        varchar tracking_number UK
        timestamp shipped_date
        timestamp delivery_date
    }

    customers ||--o{ orders : "places"
    categories ||--o{ products : "classifies"
    suppliers ||--o{ products : "supplies"
    products ||--o{ inventory : "stocked in"
    products ||--o{ order_items : "included in"
    stores ||--o{ inventory : "manages"
    stores ||--o{ orders : "processes"
    orders ||--o{ order_items : "contains"
    orders ||--o| payments : "paid via"
    orders ||--o| shipments : "shipped via"
```

### Relaciones principales

| Relacion | Tipo | Descripcion |
|---|---|---|
| `customers` -> `orders` | 1:N | Un cliente puede tener multiples ordenes |
| `categories` -> `products` | 1:N | Una categoria agrupa multiples productos |
| `suppliers` -> `products` | 1:N | Un proveedor suministra multiples productos |
| `stores` -> `inventory` | 1:N | Cada sucursal gestiona su propio inventario |
| `products` -> `inventory` | 1:N | Un producto tiene inventario en multiples tiendas |
| `orders` -> `order_items` | 1:N | Una orden contiene multiples lineas de producto |
| `orders` -> `payments` | 1:1 | Cada orden tiene un registro de pago |
| `orders` -> `shipments` | 1:1 | Cada orden tiene un registro de envio |

---

## Estructura del Proyecto

```
techstore/
├── streamlit_app.py                  # Dashboard principal (entry point Streamlit)
├── docker-compose.yml                # Orquestacion: PostgreSQL + FastAPI + Streamlit
├── Dockerfile                        # Imagen Docker multi-proposito
├── requirements.txt                  # Dependencias del backend
├── requirements-dashboard.txt        # Dependencias del dashboard
├── alembic.ini                       # Configuracion de Alembic
│
├── app/                              # Backend FastAPI
│   ├── main.py                       # Application factory, routers, middleware
│   ├── api/                          # API Layer - Endpoints REST
│   │   ├── customers.py              # CRUD + filtros para clientes
│   │   ├── products.py               # CRUD + busqueda para productos
│   │   ├── categories.py             # CRUD para categorias
│   │   ├── suppliers.py              # CRUD para proveedores
│   │   ├── stores.py                 # CRUD para sucursales
│   │   ├── inventory.py              # CRUD + low-stock + out-of-stock
│   │   ├── orders.py                 # CRUD + status transitions
│   │   ├── payments.py               # CRUD + method stats
│   │   ├── shipments.py              # CRUD + delivery performance
│   │   └── analytics.py              # 10 endpoints analiticos
│   ├── services/                     # Service Layer - Logica de negocio
│   │   ├── customer_service.py
│   │   ├── product_service.py
│   │   ├── category_service.py
│   │   ├── supplier_service.py
│   │   ├── store_service.py
│   │   ├── inventory_service.py
│   │   ├── order_service.py
│   │   ├── payment_service.py
│   │   ├── shipment_service.py
│   │   └── analytics_service.py
│   ├── repositories/                 # Repository Layer - Acceso a datos
│   │   ├── base_repository.py        # CRUD generico
│   │   ├── customer_repository.py
│   │   ├── product_repository.py
│   │   ├── category_repository.py
│   │   ├── supplier_repository.py
│   │   ├── store_repository.py
│   │   ├── inventory_repository.py
│   │   ├── order_repository.py
│   │   ├── payment_repository.py
│   │   ├── shipment_repository.py
│   │   └── analytics_repo.py         # Consultas analiticas跨tablas
│   ├── models/                       # Model Layer - SQLAlchemy ORM
│   │   └── models.py                 # 10 modelos con relaciones y constraints
│   ├── schemas/                      # Pydantic schemas
│   │   └── schemas.py                # Create, Update, Response + Analytics + Pagination
│   ├── database/                     # Configuracion de base de datos
│   │   └── config.py                 # Engine, SessionLocal, get_db dependency
│   ├── analytics/                    # Modulo de analiticas avanzadas
│   └── utils/                        # Utilidades compartidas
│
├── dashboard/                        # Dashboard Streamlit
│   ├── data_loader.py                # DataLoader dual (PostgreSQL / CSV demo)
│   ├── pages/                        # Paginas del dashboard
│   │   ├── executive_summary.py      # Resumen ejecutivo con KPIs
│   │   ├── sales.py                  # Analisis de ventas
│   │   ├── customers.py              # Analisis de clientes
│   │   ├── products.py               # Analisis de productos
│   │   ├── inventory.py              # Estado de inventario
│   │   └── sql_showcase.py           # Consultas SQL avanzadas
│   └── components/                   # Componentes reutilizables
│       ├── charts.py                 # Graficos Plotly
│       └── kpi_cards.py              # Tarjetas de KPIs
│
├── sql/                              # Scripts SQL
│   ├── schema.sql                    # DDL completo (10 tablas con constraints)
│   ├── indexes.sql                   # Indices optimizados
│   ├── views.sql                     # Vistas para consultas analiticas
│   └── showcase_queries.sql          # 20 consultas SQL avanzadas
│
├── alembic/                          # Migraciones de base de datos
│   ├── env.py                        # Configuracion de Alembic
│   └── script.py.mako                # Template para migraciones
│
├── scripts/                          # Scripts de utilidad
│   ├── seed_database.py              # Seeder con Faker (10K+ registros)
│   └── generate_demo_csv.py          # Generador de CSV para modo demo
│
├── tests/                            # Tests con Pytest
│   ├── conftest.py                   # Fixtures compartidas
│   ├── test_customers.py             # Tests de endpoints de clientes
│   ├── test_products.py              # Tests de endpoints de productos
│   ├── test_orders.py                # Tests de endpoints de ordenes
│   ├── test_analytics.py             # Tests de endpoints analiticos
│   └── test_database.py              # Tests de conexion y modelos
│
├── data/demo/                        # CSV para modo demo (sin PostgreSQL)
│
├── docs/                             # Documentacion tecnica
│   ├── erd.md                        # Diagrama Entidad-Relacion
│   └── architecture.md               # Arquitectura del sistema
│
└── .streamlit/                       # Configuracion de Streamlit
    └── secrets.example.toml          # Template de secrets
```

---

## Endpoints Principales

Todos los endpoints estan bajo el prefijo `/api/v1/`. La API genera documentacion automatica en **Swagger UI** (`/docs`) y **ReDoc** (`/redoc`).

### CRUD Endpoints

| Entidad | Metodo | Endpoint | Descripcion |
|---|---|---|---|
| **Customers** | `POST` | `/api/v1/customers` | Crear cliente (email unico) |
| | `GET` | `/api/v1/customers` | Listar clientes (paginado, filtros: city, country) |
| | `GET` | `/api/v1/customers/{id}` | Obtener cliente por ID |
| | `PUT` | `/api/v1/customers/{id}` | Actualizar cliente |
| | `DELETE` | `/api/v1/customers/{id}` | Eliminar cliente |
| **Products** | `POST` | `/api/v1/products` | Crear producto (SKU unico) |
| | `GET` | `/api/v1/products` | Listar productos (paginado, busqueda, filtros) |
| | `GET` | `/api/v1/products/{id}` | Obtener producto por ID |
| | `PUT` | `/api/v1/products/{id}` | Actualizar producto |
| | `DELETE` | `/api/v1/products/{id}` | Eliminar producto |
| **Categories** | `POST` | `/api/v1/categories` | Crear categoria (nombre unico) |
| | `GET` | `/api/v1/categories` | Listar categorias |
| | `GET` | `/api/v1/categories/{id}` | Obtener categoria por ID |
| | `PUT` | `/api/v1/categories/{id}` | Actualizar categoria |
| | `DELETE` | `/api/v1/categories/{id}` | Eliminar categoria |
| **Suppliers** | `POST` | `/api/v1/suppliers` | Crear proveedor |
| | `GET` | `/api/v1/suppliers` | Listar proveedores |
| | `GET` | `/api/v1/suppliers/{id}` | Obtener proveedor por ID |
| | `PUT` | `/api/v1/suppliers/{id}` | Actualizar proveedor |
| | `DELETE` | `/api/v1/suppliers/{id}` | Eliminar proveedor |
| **Stores** | `POST` | `/api/v1/stores` | Crear sucursal |
| | `GET` | `/api/v1/stores` | Listar sucursales |
| | `GET` | `/api/v1/stores/{id}` | Obtener sucursal por ID |
| | `PUT` | `/api/v1/stores/{id}` | Actualizar sucursal |
| | `DELETE` | `/api/v1/stores/{id}` | Eliminar sucursal |
| **Inventory** | `POST` | `/api/v1/inventory` | Crear registro de inventario |
| | `GET` | `/api/v1/inventory` | Listar inventario |
| | `GET` | `/api/v1/inventory/low-stock` | Productos con stock bajo |
| | `GET` | `/api/v1/inventory/out-of-stock` | Productos sin stock |
| | `GET` | `/api/v1/inventory/by-store/{store_id}` | Inventario por sucursal |
| **Orders** | `POST` | `/api/v1/orders` | Crear orden con items (total auto-calculado) |
| | `GET` | `/api/v1/orders` | Listar ordenes (filtros: status, customer, store, fechas) |
| | `GET` | `/api/v1/orders/{id}` | Obtener orden con items |
| | `PUT` | `/api/v1/orders/{id}/status` | Actualizar status de la orden |
| | `POST` | `/api/v1/orders/{id}/items` | Agregar item a orden existente |
| **Payments** | `POST` | `/api/v1/payments` | Crear pago |
| | `GET` | `/api/v1/payments` | Listar pagos |
| | `GET` | `/api/v1/payments/methods-stats` | Estadisticas por metodo de pago |
| **Shipments** | `POST` | `/api/v1/shipments` | Crear envio |
| | `GET` | `/api/v1/shipments` | Listar envios |
| | `GET` | `/api/v1/shipments/pending` | Envios pendientes |
| | `GET` | `/api/v1/shipments/delivery-performance` | Metricas de entrega |

### Analytics Endpoints

| Metodo | Endpoint | Descripcion |
|---|---|---|
| `GET` | `/api/v1/analytics/dashboard-summary` | KPIs generales: ventas totales, ordenes, clientes, margen |
| `GET` | `/api/v1/analytics/top-products` | Productos mas vendidos (parametro: `limit`) |
| `GET` | `/api/v1/analytics/top-customers` | Clientes con mayor gasto (parametro: `limit`) |
| `GET` | `/api/v1/analytics/monthly-sales` | Ventas mensuales |
| `GET` | `/api/v1/analytics/category-sales` | Ventas por categoria |
| `GET` | `/api/v1/analytics/inventory-status` | Estado del inventario |
| `GET` | `/api/v1/analytics/store-performance` | Rendimiento por sucursal |
| `GET` | `/api/v1/analytics/product-profitability` | Rentabilidad por producto |
| `GET` | `/api/v1/analytics/payment-methods` | Estadisticas de metodos de pago |
| `GET` | `/api/v1/analytics/delivery-performance` | Metricas de rendimiento de entregas |

### Health Check

| Metodo | Endpoint | Descripcion |
|---|---|---|
| `GET` | `/health` | Estado del servicio, version y nombre |

---

## SQL Showcase

El archivo `sql/showcase_queries.sql` contiene **20 consultas SQL avanzadas** completamente documentadas, cada una con su proposito de negocio, las caracteristicas SQL demostradas y las columnas de salida esperadas.

### Consultas incluidas

| # | Consulta | Caracteristicas SQL |
|---|---|---|
| 1 | Top 10 productos mas vendidos | `RANK() OVER`, `JOIN`, `GROUP BY`, `SUM`, `LIMIT` |
| 2 | Clientes con mayor gasto | `RANK() OVER`, `COALESCE`, `JOIN` multiple, agregacion |
| 3 | Ventas mensuales | `EXTRACT()`, `TO_CHAR()`, `DATE_TRUNC`, `GROUP BY` |
| 4 | Ventas por categoria | `JOIN` multiple, `SUM`, `COUNT DISTINCT`, `ORDER BY` |
| 5 | Ventas por proveedor | `LEFT JOIN`, `COALESCE`, subconsulta |
| 6 | Ticket promedio | CTE, `UNION ALL`, `LATERAL JOIN` |
| 7 | Productos sin ventas | `LEFT JOIN` + `IS NULL` |
| 8 | Productos con bajo stock | `CASE WHEN`, CTE, filtros condicionales |
| 9 | Inventario por tienda | `SUM` condicional, `COUNT`, valuacion de inventario |
| 10 | Ranking de tiendas | Multiples CTEs, `LAG()`, `RANK()` |
| 11 | Margen bruto por producto | Aritmetica, `CASE` para clasificacion de margenes |
| 12 | Margen bruto por categoria | CTE, `RANK()`, rollup por categoria |
| 13 | Clientes recurrentes | `HAVING`, `LAG()`, segmentacion |
| 14 | Crecimiento mensual de ventas | `LAG()`, tasa de crecimiento %, tendencia |
| 15 | Participacion por categoria | `SUM() OVER` acumulativa, `RANK()`, concentracion |
| 16 | Productos con caida de ventas | Multiples CTEs, `LAG() PARTITION`, severidad |
| 17 | Ordenes pendientes de envio | `LEFT JOIN` + `IS NULL`, estado SLA |
| 18 | Metodos de pago mas usados | `COUNT` condicional, tasa de fallo, `RANK()` |
| 19 | Promedio de dias de entrega | `EXTRACT(EPOCH)`, CTE, rating de rendimiento |
| 20 | Cohorte de clientes por mes | Pipeline de 5 CTEs, retencion %, tiers de cohorte |

---

## Como Correr Localmente

### Prerrequisitos

- **Python 3.12+** - [Descargar](https://www.python.org/downloads/)
- **PostgreSQL 16+** - [Descargar](https://www.postgresql.org/download/)
- **Docker** (opcional) - [Descargar](https://www.docker.com/products/docker-desktop/)

---

### Sin Docker

#### 1. Clonar el repositorio

```bash
git clone https://github.com/omar11011/techstore-analytics.git
cd techstore-analytics
```

#### 2. Crear entorno virtual

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

#### 3. Instalar dependencias

```bash
pip install -r requirements.txt
pip install -r requirements-dashboard.txt
```

#### 4. Configurar variables de entorno

Crear un archivo `.env` en la raiz del proyecto:

```env
DATABASE_URL=postgresql://techstore:techstore@localhost:5432/techstore
```

O exportar la variable directamente:

```bash
export DATABASE_URL="postgresql://techstore:techstore@localhost:5432/techstore"
```

#### 5. Crear la base de datos PostgreSQL

```bash
# Conectar a PostgreSQL
psql -U postgres

# Crear usuario y base de datos
CREATE USER techstore WITH PASSWORD 'techstore';
CREATE DATABASE techstore OWNER techstore;
GRANT ALL PRIVILEGES ON DATABASE techstore TO techstore;
\q
```

#### 6. Ejecutar migraciones

```bash
alembic upgrade head
```

#### 7. Poblar la base de datos (seed)

```bash
# Con valores por defecto: 1000 clientes, 500 productos, 10000 ordenes
python scripts/seed_database.py

# Con opciones personalizadas
python scripts/seed_database.py --orders 5000 --seed 42
```

#### 8. Iniciar FastAPI

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

La API estara disponible en:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### 9. Iniciar Streamlit Dashboard

```bash
streamlit run streamlit_app.py
```

El dashboard estara disponible en http://localhost:8501

---

### Con Docker

La forma mas sencilla de levantar todo el proyecto es con Docker Compose:

```bash
docker compose up
```

Esto inicia automaticamente:

| Servicio | Puerto | Descripcion |
|---|---|---|
| **postgres** | 5432 | Base de datos PostgreSQL 16 con volumen persistente |
| **fastapi** | 8000 | API REST con hot-reload |
| **streamlit** | 8501 | Dashboard analitico interactivo |

Para ejecutar en segundo plano:

```bash
docker compose up -d
```

Para detener todos los servicios:

```bash
docker compose down
```

La primera vez que levantes los contenedores, necesitaras ejecutar las migraciones y el seeder dentro del contenedor de FastAPI:

```bash
docker compose exec fastapi alembic upgrade head
docker compose exec fastapi python scripts/seed_database.py
```

---

## Como Usar el Dashboard

```bash
streamlit run streamlit_app.py
```

### Paginas del Dashboard

| Pagina | Descripcion |
|---|---|
| **Resumen Ejecutivo** | KPIs principales: ventas totales, ordenes, clientes, ticket promedio, margen bruto. Graficos de tendencias mensuales y distribucion por categoria. |
| **Ventas** | Analisis detallado: evolucion mensual, comparativas por periodo, distribucion por categoria y sucursal, top productos vendidos. |
| **Clientes** | Top clientes por gasto, distribucion geografica, frecuencia de compra, valor de vida del cliente. |
| **Productos** | Rentabilidad, margenes por categoria, distribucion de precios, rotacion de inventario. |
| **Inventario** | Productos con stock bajo, sin stock, sobre-stock, distribucion por tienda y categoria. |
| **SQL Showcase** | Las 20 consultas SQL avanzadas con explicacion, codigo SQL y resultados. |

### Filtros Disponibles

El sidebar del dashboard incluye filtros globales que afectan a todas las paginas:

- **Rango de Fechas** - Filtra datos por periodo temporal
- **Categoria** - Filtra por categoria de producto
- **Sucursal** - Filtra por sucursal/tienda

### Indicador de Conexion

El sidebar muestra el estado de la conexion a la base de datos:
- **Modo: PostgreSQL** - Conectado a la base de datos activa
- **Modo: CSV Demo** - Usando datos de ejemplo (sin PostgreSQL)

---

## Como Desplegar en Streamlit Community Cloud

Streamlit Community Cloud permite desplegar el dashboard gratuitamente sin necesidad de servidor propio. El modo demo (CSV) hace que el dashboard funcione automaticamente sin base de datos.

### Pasos para desplegar

#### 1. Subir el repositorio a GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/omar11011/techstore-analytics.git
git push -u origin main
```

#### 2. Acceder a Streamlit Community Cloud

Ir a [share.streamlit.io](https://share.streamlit.io/) e iniciar sesion con tu cuenta de GitHub.

#### 3. Crear una nueva aplicacion

Hacer clic en **"New app"** y seleccionar:
- **Repository**: `omar11011/techstore-analytics`
- **Branch**: `main`
- **Main file path**: `streamlit_app.py`

#### 4. Configurar secrets (opcional, para conectar a PostgreSQL)

Si deseas conectar a una base de datos PostgreSQL remota (Supabase, Railway, Neon), agrega los secrets. De lo contrario, el dashboard funcionara en **modo demo** con los CSV incluidos.

#### 5. Desplegar

Hacer clic en **"Deploy"**. En unos minutos el dashboard estara disponible en una URL publica como:

```
https://omar11011-techstore-analytics-streamlit-app.streamlit.app
```

### Archivo de secrets de ejemplo

Crear `.streamlit/secrets.toml` con el siguiente contenido:

```toml
# .streamlit/secrets.toml
# Para modo demo, simplemente omite este archivo.

[database]
url = "postgresql://usuario:password@host:5432/techstore"
```

Nunca subas el archivo `secrets.toml` a GitHub. Esta incluido en el `.gitignore`.

---

## Modo Demo

Una de las caracteristicas mas utiles del proyecto es el **modo demo automatico**: si no hay una conexion PostgreSQL disponible, el dashboard detecta la situacion y carga automaticamente los datos CSV desde el directorio `data/demo/`.

### Como funciona

1. Al iniciar, el `DataLoader` intenta conectarse a PostgreSQL usando `st.secrets` o la variable de entorno `DATABASE_URL`.
2. Si la conexion falla (o no esta configurada), cambia automaticamente a modo demo.
3. Se muestra un banner indicando que se esta usando datos CSV de ejemplo.
4. Todas las funcionalidades del dashboard siguen operando con los datos de ejemplo.

### Ventajas del modo demo

- **Deploy en Streamlit Community Cloud** sin necesidad de base de datos externa.
- **Presentaciones de portafolio** donde no se quiere exponer credenciales.
- **Desarrollo local** sin configurar PostgreSQL.
- **Pruebas rapidas** de la interfaz sin datos reales.

### Generar datos de demostracion

```bash
python scripts/generate_demo_csv.py
```

Esto genera los archivos CSV en `data/demo/` con datos realistas usando Faker.

---

## Configuracion de Secrets

### Para desarrollo local (`.env`)

```env
DATABASE_URL=postgresql://techstore:techstore@localhost:5432/techstore
```

### Para Streamlit Cloud (`.streamlit/secrets.toml`)

```toml
[database]
url = "postgresql://techstore:techstore@localhost:5432/techstore"
```

### Para Docker Compose

La variable `DATABASE_URL` se configura directamente en el archivo `docker-compose.yml`:

```yaml
environment:
  DATABASE_URL: postgresql://techstore:techstore@postgres:5432/techstore
```

El host `postgres` en Docker Compose se refiere al servicio de PostgreSQL dentro de la red de Docker, no a `localhost`.

---

## Aprendizajes Demostrados

### Base de Datos y SQL
- SQL avanzado - CTEs (`WITH`), Window Functions (`RANK`, `LAG`, `ROW_NUMBER`, `SUM OVER`), subconsultas correlacionadas
- Diseno de bases de datos relacionales normalizadas - 10 tablas en 3FN con relaciones 1:1, 1:N y M:N
- Integridad referencial - Foreign Keys con `ON DELETE CASCADE/SET NULL/RESTRICT`
- CHECK constraints - Validacion a nivel de base de datos
- Indices optimizados - Indices en columnas de busqueda frecuente y claves foraneas
- Vistas - Vistas para consultas analiticas frecuentes

### Backend y API
- Backend profesional con FastAPI - Application factory, lifespan, middleware, CORS
- APIs REST con validacion - Pydantic v2 con `field_validator` y `model_validator`
- Documentacion automatica - Swagger UI y ReDoc generados desde los schemas
- Paginacion - Wrapper generico `PaginatedResponse[T]` con metadatos
- Manejo robusto de errores - Exception handlers globales, HTTP status codes apropiados
- Middleware - Timing header (`X-Process-Time`), CORS configurado

### Arquitectura y Patrones
- Patron Repository - `BaseRepository` generico con CRUD para todas las entidades
- Separacion de responsabilidades - API -> Service -> Repository -> Model -> DB
- Inyeccion de dependencias - `Depends(get_db)` para sesiones de base de datos
- Principio DRY - Codigo generico reutilizable, sin duplicacion

### Visualizacion y Dashboard
- Dashboard analitico con Streamlit - 6 paginas con navegacion, filtros y modo dual
- Visualizacion de datos con Plotly - Graficos interactivos (barras, lineas, pie)
- CSS personalizado - Sidebar oscuro, tarjetas de KPIs estilizadas
- DataLoader dual - PostgreSQL como fuente primaria, CSV como fallback automatico

### DevOps y Herramientas
- Contenerizacion con Docker - Dockerfile optimizado, Docker Compose con 3 servicios
- Migraciones con Alembic - Control de versiones del esquema de base de datos
- Testing con Pytest - Tests de API, modelos, servicios y analiticas
- Generacion de datos - Faker para datos realistas, seeder parametrizable
- Deploy en la nube - Compatible con Streamlit Community Cloud, Railway, etc.

### Calidad de Codigo
- Codigo limpio y profesional - Type hints, docstrings, logging estructurado
- Tipado estricto - Python type hints y Pydantic
- Convenciones - PEP 8, nombres descriptivos, organizacion consistente

---