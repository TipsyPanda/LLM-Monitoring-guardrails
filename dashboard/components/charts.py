"""Chart components using Plotly"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

from dashboard.config import config
from dashboard.data.processor import DataProcessor


def render_time_series(
    df: pd.DataFrame,
    title: str = "Violations Over Time",
    color_column: str = "severity",
    freq: str = "H"
):
    """
    Render time series line chart

    Args:
        df: DataFrame with timestamp and severity/danger_level columns
        title: Chart title
        color_column: Column to use for color grouping
        freq: Time aggregation frequency
    """
    if df.empty:
        st.info(f"No data available for {title}")
        return

    # Aggregate by time
    agg_df = DataProcessor.aggregate_by_time(df, freq=freq, value_column=color_column)

    if agg_df.empty:
        st.info(f"No data available for {title}")
        return

    # Select color map based on column
    if color_column == "severity":
        color_map = config.SEVERITY_COLORS
    elif color_column == "danger_level":
        color_map = config.DANGER_COLORS
    else:
        color_map = None

    fig = px.line(
        agg_df,
        x='period',
        y='count',
        color=color_column if color_column in agg_df.columns else None,
        color_discrete_map=color_map,
        title=title,
        markers=True
    )

    fig.update_layout(
        height=config.CHART_HEIGHT,
        xaxis_title="Time",
        yaxis_title="Count",
        legend_title=color_column.replace("_", " ").title() if color_column else None
    )

    st.plotly_chart(fig, use_container_width=True)


def render_label_distribution(df: pd.DataFrame, title: str = "Toxicity Label Distribution"):
    """
    Render horizontal bar chart of toxicity label counts

    Args:
        df: DataFrame with toxicity_labels column
        title: Chart title
    """
    if df.empty:
        st.info("No data available for label distribution")
        return

    label_counts = DataProcessor.get_label_counts(df)

    # Create DataFrame for plotting
    labels_df = pd.DataFrame([
        {"label": label, "count": count}
        for label, count in label_counts.items()
    ])

    # Sort by count descending
    labels_df = labels_df.sort_values('count', ascending=True)

    fig = px.bar(
        labels_df,
        x='count',
        y='label',
        orientation='h',
        title=title,
        color='label',
        color_discrete_map=config.TOXICITY_LABEL_COLORS
    )

    fig.update_layout(
        height=config.CHART_HEIGHT,
        xaxis_title="Count",
        yaxis_title="Toxicity Label",
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)


def render_severity_pie(df: pd.DataFrame, title: str = "Severity Distribution"):
    """
    Render pie/donut chart of severity distribution

    Args:
        df: DataFrame with severity column
        title: Chart title
    """
    if df.empty:
        st.info("No data available for severity distribution")
        return

    severity_counts = DataProcessor.get_severity_distribution(df)

    # Filter out zero counts
    severity_counts = {k: v for k, v in severity_counts.items() if v > 0}

    if not severity_counts:
        st.info("No severity data available")
        return

    # Create DataFrame for plotting
    severity_df = pd.DataFrame([
        {"severity": sev, "count": count}
        for sev, count in severity_counts.items()
    ])

    fig = px.pie(
        severity_df,
        values='count',
        names='severity',
        title=title,
        color='severity',
        color_discrete_map=config.SEVERITY_COLORS,
        hole=0.4  # Donut chart
    )

    fig.update_layout(height=config.CHART_HEIGHT)
    fig.update_traces(textposition='inside', textinfo='percent+label')

    st.plotly_chart(fig, use_container_width=True)


def render_danger_pie(df: pd.DataFrame, title: str = "Alert Danger Level Distribution"):
    """
    Render pie/donut chart of danger level distribution

    Args:
        df: DataFrame with danger_level column
        title: Chart title
    """
    if df.empty:
        st.info("No alert data available")
        return

    danger_counts = DataProcessor.get_danger_distribution(df)

    # Filter out zero counts
    danger_counts = {k: v for k, v in danger_counts.items() if v > 0}

    if not danger_counts:
        st.info("No danger level data available")
        return

    # Create DataFrame for plotting
    danger_df = pd.DataFrame([
        {"danger_level": level, "count": count}
        for level, count in danger_counts.items()
    ])

    fig = px.pie(
        danger_df,
        values='count',
        names='danger_level',
        title=title,
        color='danger_level',
        color_discrete_map=config.DANGER_COLORS,
        hole=0.4
    )

    fig.update_layout(height=config.CHART_HEIGHT)
    fig.update_traces(textposition='inside', textinfo='percent+label')

    st.plotly_chart(fig, use_container_width=True)


def render_score_heatmap(df: pd.DataFrame, title: str = "Toxicity Score Heatmap"):
    """
    Render heatmap of toxicity scores

    Args:
        df: DataFrame with metadata column containing scores
        title: Chart title
    """
    if df.empty:
        st.info("No data available for score heatmap")
        return

    scores_df = DataProcessor.extract_scores(df)

    if scores_df.empty:
        st.info("No score data available")
        return

    # Limit to last 20 records for readability
    scores_df = scores_df.tail(20)

    # Create heatmap data
    score_columns = config.TOXICITY_LABELS
    heatmap_data = scores_df[score_columns].values

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=score_columns,
        y=[f"{row['conversation_id'][:12]}" for _, row in scores_df.iterrows()],
        colorscale='RdYlGn_r',
        zmin=0,
        zmax=1
    ))

    fig.update_layout(
        title=title,
        height=max(config.CHART_HEIGHT, len(scores_df) * 25),
        xaxis_title="Toxicity Category",
        yaxis_title="Conversation"
    )

    st.plotly_chart(fig, use_container_width=True)
