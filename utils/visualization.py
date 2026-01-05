"""
Visualization utilities
Plotly chart builders for clinical data
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Optional


def create_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
    color: str = '#1f77b4'
) -> go.Figure:
    """
    Create a Plotly bar chart.

    Args:
        df: DataFrame containing the data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
        color: Bar color (hex)

    Returns:
        Plotly Figure object
    """
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        title=title,
        labels={x_col: x_col, y_col: y_col},
        color_discrete_sequence=[color]
    )
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=y_col,
        hovermode='x unified'
    )
    return fig


def create_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = ""
) -> go.Figure:
    """
    Create a Plotly line chart.

    Args:
        df: DataFrame containing the data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title

    Returns:
        Plotly Figure object
    """
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        title=title,
        labels={x_col: x_col, y_col: y_col},
        markers=True
    )
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=y_col,
        hovermode='x unified'
    )
    return fig


def render_chart_from_recipe(df: pd.DataFrame, recipe: Dict) -> None:
    """
    Render chart based on recipe visualization metadata using Streamlit.

    Args:
        df: DataFrame containing the data
        recipe: Recipe configuration dict with 'visualization' key
    """
    import streamlit as st

    viz_info = recipe.get("visualization")

    if viz_info:
        chart_type = viz_info.get("chart_type")
        chart_title = viz_info.get("title", "")

        try:
            if chart_type == "bar_chart":
                x_col = viz_info.get("x_column")
                y_col = viz_info.get("y_column")
                fig = create_bar_chart(df, x_col, y_col, chart_title)
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "line_chart":
                x_col = viz_info.get("x_column")
                y_col = viz_info.get("y_column")
                fig = create_line_chart(df, x_col, y_col, chart_title)
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "metric":
                # For single-row dataframes, display each column as a metric
                if not df.empty:
                    cols = st.columns(len(df.columns))
                    for j, col_name in enumerate(df.columns):
                        cols[j].metric(label=col_name, value=df.iloc[0][col_name])
                else:
                    st.warning("Data is empty, cannot display metrics.")

            else:  # Default to table
                st.write("**Parsed Data Table:**")
                st.dataframe(df)

        except Exception as e:
            st.error(f"Failed to generate chart: {e}")
            st.write("Displaying raw data instead:")
            st.dataframe(df)
    else:
        st.write("No visualization info in recipe. Displaying raw data table.")
        st.dataframe(df)
