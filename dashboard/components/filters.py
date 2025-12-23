"""Sidebar filter components"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any

from dashboard.config import config


def render_sidebar() -> Dict[str, Any]:
    """
    Render sidebar filter controls

    Returns:
        Dictionary of filter values
    """
    st.sidebar.header("Filters")

    filters = {}

    # Data source selector
    filters['source'] = st.sidebar.radio(
        "Data Source",
        options=["both", "batch", "kafka"],
        format_func=lambda x: {
            "both": "All Sources",
            "batch": "Batch (CSV)",
            "kafka": "Kafka (Real-time)"
        }.get(x, x),
        index=0
    )

    st.sidebar.divider()

    # Date range
    st.sidebar.subheader("Date Range")

    default_start = datetime.now() - timedelta(days=7)
    default_end = datetime.now()

    col1, col2 = st.sidebar.columns(2)
    with col1:
        filters['start_date'] = st.date_input(
            "Start",
            value=default_start,
            key="start_date"
        )
    with col2:
        filters['end_date'] = st.date_input(
            "End",
            value=default_end,
            key="end_date"
        )

    # Convert dates to datetime
    if filters['start_date']:
        filters['start_date'] = datetime.combine(filters['start_date'], datetime.min.time())
    if filters['end_date']:
        filters['end_date'] = datetime.combine(filters['end_date'], datetime.max.time())

    st.sidebar.divider()

    # Severity filter
    st.sidebar.subheader("Severity")
    filters['severities'] = st.sidebar.multiselect(
        "Select Severity Levels",
        options=config.SEVERITY_LEVELS,
        default=config.SEVERITY_LEVELS,
        key="severity_filter"
    )

    st.sidebar.divider()

    # Toxicity label filter
    st.sidebar.subheader("Toxicity Labels")
    filters['labels'] = st.sidebar.multiselect(
        "Select Labels",
        options=config.TOXICITY_LABELS,
        default=[],
        key="label_filter",
        help="Leave empty to show all labels"
    )

    # If empty, set to None to not filter
    if not filters['labels']:
        filters['labels'] = None

    st.sidebar.divider()

    # Conversation ID search
    filters['conversation_id'] = st.sidebar.text_input(
        "Search Conversation ID",
        value="",
        key="conv_id_search",
        help="Partial match search"
    )

    if not filters['conversation_id']:
        filters['conversation_id'] = None

    st.sidebar.divider()

    # Minimum score threshold
    filters['min_score'] = st.sidebar.slider(
        "Minimum Toxicity Score",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        key="min_score"
    )

    st.sidebar.divider()

    # Time aggregation for charts
    filters['time_aggregation'] = st.sidebar.selectbox(
        "Time Aggregation",
        options=["H", "D"],
        format_func=lambda x: {"H": "Hourly", "D": "Daily"}.get(x, x),
        index=0,
        key="time_agg"
    )

    st.sidebar.divider()

    # Auto-refresh controls
    st.sidebar.subheader("Auto Refresh")

    filters['auto_refresh'] = st.sidebar.toggle(
        "Enable Auto Refresh",
        value=False,
        key="auto_refresh"
    )

    if filters['auto_refresh']:
        filters['refresh_interval'] = st.sidebar.selectbox(
            "Refresh Interval (seconds)",
            options=config.REFRESH_INTERVALS,
            index=2,  # Default to 30 seconds
            key="refresh_interval"
        )
    else:
        filters['refresh_interval'] = config.DEFAULT_REFRESH_INTERVAL

    # Manual refresh button
    if st.sidebar.button("Refresh Now", key="manual_refresh"):
        st.cache_data.clear()
        st.rerun()

    return filters


def render_data_info(file_stats: Dict[str, Dict]):
    """
    Render data file information in sidebar

    Args:
        file_stats: Dictionary of file statistics
    """
    st.sidebar.divider()
    st.sidebar.subheader("Data Files")

    for filename, stats in file_stats.items():
        if stats.get('exists'):
            modified = stats.get('modified')
            if modified:
                time_str = modified.strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = "Unknown"

            size_kb = stats.get('size', 0) / 1024
            st.sidebar.caption(f"**{filename}**")
            st.sidebar.caption(f"  Modified: {time_str}")
            st.sidebar.caption(f"  Size: {size_kb:.1f} KB")
        else:
            st.sidebar.caption(f"**{filename}**: Not found")
