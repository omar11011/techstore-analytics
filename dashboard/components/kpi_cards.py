"""
TechStore Analytics — KPI Card Components
==========================================
Professional metric cards for the executive dashboard.
Provides reusable KPI rendering functions with consistent formatting.
"""

from __future__ import annotations

import streamlit as st


def render_kpi_card(
    label: str,
    value: str | float | int,
    delta: str | None = None,
    prefix: str = "$",
    is_percentage: bool = False,
) -> None:
    """Render a single KPI metric card using st.metric.

    Args:
        label: Display label for the metric.
        value: Numeric or string value to display.
        delta: Optional delta/change indicator.
        prefix: Currency or unit prefix (default "$").
        is_percentage: If True, format as percentage.
    """
    if is_percentage:
        formatted = f"{value:,.1f}%"
    elif isinstance(value, (int, float)) and prefix == "$":
        formatted = f"${value:,.2f}"
    elif isinstance(value, (int, float)):
        formatted = f"{value:,}"
    else:
        formatted = str(value)

    st.metric(label=label, value=formatted, delta=delta)


def render_kpi_row(metrics_list: list[dict]) -> None:
    """Render a row of KPI cards from a list of metric definitions.

    Args:
        metrics_list: List of dicts with keys:
            - label (str): Display name
            - value (str|float|int): The metric value
            - delta (str|None, optional): Change indicator
            - prefix (str, optional): Unit prefix, default "$"
            - is_percentage (bool, optional): Format as percentage
    """
    n = len(metrics_list)
    if n == 0:
        return

    cols = st.columns(n)

    for col, metric in zip(cols, metrics_list):
        with col:
            render_kpi_card(
                label=metric.get("label", ""),
                value=metric.get("value", 0),
                delta=metric.get("delta"),
                prefix=metric.get("prefix", "$"),
                is_percentage=metric.get("is_percentage", False),
            )
