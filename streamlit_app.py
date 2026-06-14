"""
TechStore Analytics — Main Streamlit Application
==================================================
Dashboard principal con navegación por sidebar, filtros y modo dual
(PostgreSQL / CSV demo).
"""

from __future__ import annotations

import pathlib
import sys

# Ensure project root is on sys.path so `dashboard.*` imports work
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import streamlit as st

from dashboard.data_loader import DataLoader, CHART_COLORS

# ---------------------------------------------------------------------------
# Page config (MUST be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="TechStore Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Professional dark sidebar, clean metrics, polished look
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stRadio > label {
        color: #ffffff !important;
        font-weight: 600;
    }
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.15rem;
    }

    /* ---- Sidebar radio items ---- */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        padding: 0.55rem 0.85rem;
        border-radius: 8px;
        transition: background 0.2s, transform 0.1s;
        font-size: 0.95rem;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
        background: rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-baseweb="radio"] [class*="inner"] {
        border-color: #3b82f6 !important;
    }

    /* ---- Sidebar section headers ---- */
    [data-testid="stSidebar"] h3 {
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
        color: #94a3b8 !important;
        margin-top: 0.5rem !important;
    }

    /* ---- Metric cards ---- */
    [data-testid="stMetricValue"] {
        font-size: 1.65rem;
        font-weight: 700;
        color: #0f172a;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.85rem;
    }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    /* ---- Main container ---- */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    /* ---- Headers ---- */
    h2 {
        border-bottom: 3px solid #2563eb;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        color: #0f172a;
    }
    h3, h4 {
        color: #1e293b;
        margin-top: 1.2rem;
    }

    /* ---- Dataframe ---- */
    .stDataFrame {
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        overflow: hidden;
    }

    /* ---- Demo banner ---- */
    .demo-banner {
        background: linear-gradient(90deg, #fef3c7 0%, #fef9c3 100%);
        border-left: 4px solid #f59e0b;
        padding: 0.85rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 1.25rem;
        color: #92400e;
        font-size: 0.95rem;
    }

    /* ---- Footer ---- */
    .footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.8rem;
        padding: 1.5rem 0;
        border-top: 1px solid #e2e8f0;
        margin-top: 2.5rem;
    }

    /* ---- Plotly chart containers ---- */
    .js-plotly-plot .plotly .modebar {
        right: 0.5rem !important;
    }

    /* ---- Dividers ---- */
    hr {
        border-color: #e2e8f0;
    }

    /* ---- Selectbox styling ---- */
    .stSelectbox label {
        font-weight: 600;
        color: #334155;
    }

    /* ---- Expander ---- */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1e293b;
    }

    /* ---- Sidebar filter labels ---- */
    [data-testid="stSidebar"] label {
        font-size: 0.9rem !important;
    }

    /* ---- Scrollbar styling ---- */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Initialize DataLoader
# ---------------------------------------------------------------------------
@st.cache_resource
def get_loader() -> DataLoader:
    return DataLoader()

loader = get_loader()

# ---------------------------------------------------------------------------
# Demo mode banner
# ---------------------------------------------------------------------------
if loader.is_demo_mode():
    st.markdown(
        '<div class="demo-banner">'
        '⚠️ <strong>Modo Demo</strong> — Usando datos CSV de ejemplo. '
        'Configura <code>DATABASE_URL</code> para conectar a PostgreSQL.'
        '</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Sidebar — Navigation + Filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("# 📊 TechStore")
    st.markdown("### Analytics Dashboard")
    st.divider()

    page = st.radio(
        "Navegación",
        options=[
            "📊 Resumen Ejecutivo",
            "💰 Ventas",
            "👥 Clientes",
            "🛍️ Productos",
            "📦 Inventario",
            "🗄️ SQL Showcase",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.divider()

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    st.markdown("### 🔍 Filtros")

    # Date range
    orders_df = loader.get_orders()
    date_range = None
    if not orders_df.empty and "order_date" in orders_df.columns:
        orders_df["order_date"] = pd.to_datetime(orders_df["order_date"], errors="coerce")
        min_date = orders_df["order_date"].min().date()
        max_date = orders_df["order_date"].max().date()
        date_range = st.date_input(
            "📅 Rango de Fechas",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

    # Category filter
    categories_df = loader.get_categories()
    selected_category = None
    if not categories_df.empty:
        cat_col = "name" if "name" in categories_df.columns else "category_name"
        if cat_col in categories_df.columns:
            cat_options = ["Todas"] + sorted(categories_df[cat_col].dropna().unique().tolist())
            selected_category = st.selectbox("🏷️ Categoría", cat_options)

    # Store filter
    stores_df = loader.get_stores()
    selected_store = None
    if not stores_df.empty:
        store_col = "name" if "name" in stores_df.columns else "store_name"
        if store_col in stores_df.columns:
            store_options = ["Todas"] + sorted(stores_df[store_col].dropna().unique().tolist())
            selected_store = st.selectbox("🏪 Sucursal", store_options)

    # Build filters dict
    filters = {}
    if date_range and len(date_range) == 2:
        filters["date_range"] = date_range
    if selected_category and selected_category != "Todas":
        filters["category"] = selected_category
    if selected_store and selected_store != "Todas":
        filters["store"] = selected_store

    st.divider()

    # Connection info
    st.markdown("### ℹ️ Conexión")
    if loader.is_demo_mode():
        st.markdown("🔴 **Modo:** CSV Demo")
        st.markdown("📁 **Fuente:** `data/demo/`")
    else:
        st.markdown("🟢 **Modo:** PostgreSQL")
        st.markdown("🗄️ **Fuente:** Base de datos activa")

# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------
PAGE_MAP = {
    "📊 Resumen Ejecutivo": "dashboard.pages.executive_summary",
    "💰 Ventas": "dashboard.pages.sales",
    "👥 Clientes": "dashboard.pages.customers",
    "🛍️ Productos": "dashboard.pages.products",
    "📦 Inventario": "dashboard.pages.inventory",
    "🗄️ SQL Showcase": "dashboard.pages.sql_showcase",
}

module_name = PAGE_MAP[page]

# Import the page module and call render()
import importlib

page_module = importlib.import_module(module_name)
page_module.render(loader, filters)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="footer">'
    'TechStore Analytics Dashboard · Powered by Streamlit + Plotly · '
    f'{"Modo Demo (CSV)" if loader.is_demo_mode() else "PostgreSQL"} · '
    '© 2026'
    '</div>',
    unsafe_allow_html=True,
)
