"""
TechStore Analytics — Chart Components
========================================
Reusable Plotly chart builders with professional styling.
All charts use a consistent template and color palette.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Shared template & colours
# ---------------------------------------------------------------------------
CHART_COLORS = [
    "#2563eb",
    "#f59e0b",
    "#10b981",
    "#ef4444",
    "#8b5cf6",
    "#ec4899",
    "#06b6d4",
    "#f97316",
    "#6366f1",
    "#14b8a6",
]

_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, -apple-system, sans-serif", size=13, color="#374151"),
    margin=dict(l=60, r=30, t=70, b=60),
    title=dict(
        font=dict(size=18, color="#111827", family="Inter, system-ui, sans-serif"),
        x=0.03,
        xanchor="left",
    ),
)

_AXIS_DEFAULTS = dict(
    gridcolor="#f3f4f6",
    gridwidth=1,
    zeroline=False,
    title_font=dict(size=13, color="#6b7280"),
    tickfont=dict(size=12, color="#6b7280"),
    linecolor="#e5e7eb",
    linewidth=1,
)


def _apply_template(fig: go.Figure) -> go.Figure:
    """Apply consistent professional styling to a figure."""
    fig.update_layout(**_LAYOUT_DEFAULTS)
    fig.update_xaxes(**_AXIS_DEFAULTS)
    fig.update_yaxes(**_AXIS_DEFAULTS)
    return fig


# ---------------------------------------------------------------------------
# Line chart
# ---------------------------------------------------------------------------
def create_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    line_color: str = CHART_COLORS[0],
) -> go.Figure:
    """Create a professional line chart with markers.

    Args:
        df: Source DataFrame.
        x: Column name for x-axis.
        y: Column name for y-axis.
        title: Chart title.
        color: Optional column for color grouping.
        line_color: Color when no grouping is used.

    Returns:
        Plotly Figure object.
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=title, **_LAYOUT_DEFAULTS)
        fig.add_annotation(
            text="Sin datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#9ca3af"),
        )
        return fig

    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        markers=True,
        color_discrete_sequence=CHART_COLORS,
    )

    if color is None:
        fig.update_traces(
            line_color=line_color,
            line_width=2.5,
            marker_size=7,
            marker_line_width=1,
            marker_line_color="white",
        )
    else:
        fig.update_traces(
            line_width=2.5,
            marker_size=6,
            marker_line_width=1,
            marker_line_color="white",
        )

    fig.update_layout(
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=12),
        ),
    )

    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Bar chart
# ---------------------------------------------------------------------------
def create_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    orientation: str = "v",
) -> go.Figure:
    """Create a professional bar chart.

    Args:
        df: Source DataFrame.
        x: Column name for x-axis.
        y: Column name for y-axis.
        title: Chart title.
        color: Optional column for color grouping.
        orientation: 'v' for vertical, 'h' for horizontal.

    Returns:
        Plotly Figure object.
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=title, **_LAYOUT_DEFAULTS)
        fig.add_annotation(
            text="Sin datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#9ca3af"),
        )
        return fig

    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        orientation=orientation,
        color_discrete_sequence=CHART_COLORS,
    )

    fig.update_traces(
        marker_line_width=0,
        marker_opacity=0.9,
        hovertemplate="<b>%{x}</b><br>%{y:,.2f}<extra></extra>",
    )

    if orientation == "h":
        fig.update_layout(yaxis=dict(autorange="reversed"))

    fig.update_layout(
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=12),
        ),
    )

    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Pie / donut chart
# ---------------------------------------------------------------------------
def create_pie_chart(
    df: pd.DataFrame,
    values: str,
    names: str,
    title: str,
    hole: float = 0.50,
) -> go.Figure:
    """Create a professional donut chart.

    Args:
        df: Source DataFrame.
        values: Column for slice values.
        names: Column for slice labels.
        title: Chart title.
        hole: Donut hole size (0=pie, 1=no chart).

    Returns:
        Plotly Figure object.
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=title, **_LAYOUT_DEFAULTS)
        fig.add_annotation(
            text="Sin datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#9ca3af"),
        )
        return fig

    fig = px.pie(
        df,
        values=values,
        names=names,
        title=title,
        hole=hole,
        color_discrete_sequence=CHART_COLORS,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_size=12,
        hovertemplate="%{label}<br>$%{value:,.2f}<br>%{percent}<extra></extra>",
        marker_line_width=2,
        marker_line_color="white",
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=12),
        ),
    )

    return _apply_template(fig)


# ---------------------------------------------------------------------------
# Styled data table
# ---------------------------------------------------------------------------
def create_table(df: pd.DataFrame, title: str | None = None) -> None:
    """Display a styled DataFrame using st.dataframe.

    Automatically formats currency columns and sets a responsive height.

    Args:
        df: DataFrame to display.
        title: Optional title above the table.
    """
    if title:
        st.markdown(f"#### {title}")

    if df.empty:
        st.info("No hay datos disponibles para mostrar.")
        return

    display_df = df.copy()

    # Format currency columns
    for col in display_df.select_dtypes(include=["float64", "float32"]).columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in ["sales", "spent", "revenue", "amount", "total", "ticket", "cost", "price", "profit"]):
            display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else x)

    # Format percentage columns
    for col in display_df.columns:
        col_lower = col.lower()
        if "margin" in col_lower or "pct" in col_lower or "percent" in col_lower:
            try:
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.1f}%" if pd.notna(x) else x)
            except Exception:
                pass

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=min(450, max(200, len(display_df) * 35 + 40)),
    )
