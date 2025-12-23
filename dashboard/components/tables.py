"""Data table components"""

import streamlit as st
import pandas as pd
from typing import Optional

from dashboard.config import config
from dashboard.data.processor import DataProcessor


def render_violations_table(
    df: pd.DataFrame,
    page_size: int = 20,
    title: str = "Recent Violations"
):
    """
    Render interactive violations table

    Args:
        df: Violations DataFrame
        page_size: Number of rows per page
        title: Table title
    """
    st.subheader(title)

    if df.empty:
        st.info("No violations to display")
        return

    # Prepare display DataFrame
    display_df = df.copy()

    # Sort by timestamp descending
    if 'timestamp' in display_df.columns:
        display_df = display_df.sort_values('timestamp', ascending=False)

    # Create display columns
    display_data = []
    for _, row in display_df.iterrows():
        # Get top score
        top_score = DataProcessor.get_top_score(row.get('metadata', {}))

        # Format labels
        labels = row.get('toxicity_labels', [])
        if isinstance(labels, list):
            labels_str = ", ".join(labels[:3])
            if len(labels) > 3:
                labels_str += f" (+{len(labels) - 3})"
        else:
            labels_str = str(labels)

        display_data.append({
            'Timestamp': row.get('timestamp', '').strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row.get('timestamp')) else '',
            'Conversation': row.get('conversation_id', '')[:15],
            'Text': DataProcessor.truncate_text(row.get('original_text', ''), config.MAX_TEXT_LENGTH),
            'Severity': row.get('severity', '').upper(),
            'Labels': labels_str,
            'Top Score': f"{top_score:.2f}"
        })

    display_df = pd.DataFrame(display_data)

    # Pagination
    total_rows = len(display_df)
    total_pages = (total_rows - 1) // page_size + 1 if total_rows > 0 else 1

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        page = st.selectbox(
            "Page",
            options=range(1, total_pages + 1),
            format_func=lambda x: f"Page {x} of {total_pages}",
            key="violations_page"
        )

    # Get page data
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_df = display_df.iloc[start_idx:end_idx]

    # Style the dataframe
    def style_severity(val):
        if val == 'HIGH':
            return f'background-color: {config.SEVERITY_COLORS["high"]}; color: white'
        elif val == 'MEDIUM':
            return f'background-color: {config.SEVERITY_COLORS["medium"]}; color: white'
        elif val == 'LOW':
            return f'background-color: {config.SEVERITY_COLORS["low"]}; color: white'
        return ''

    styled_df = page_df.style.applymap(
        style_severity,
        subset=['Severity']
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )

    # Show record count
    st.caption(f"Showing {start_idx + 1}-{min(end_idx, total_rows)} of {total_rows} violations")


def render_alerts_table(
    df: pd.DataFrame,
    page_size: int = 15,
    title: str = "Recent Alerts"
):
    """
    Render interactive alerts table

    Args:
        df: Alerts DataFrame
        page_size: Number of rows per page
        title: Table title
    """
    st.subheader(title)

    if df.empty:
        st.info("No alerts to display")
        return

    # Prepare display DataFrame
    display_df = df.copy()

    # Sort by timestamp descending
    if 'timestamp' in display_df.columns:
        display_df = display_df.sort_values('timestamp', ascending=False)

    # Create display columns
    display_data = []
    for _, row in display_df.iterrows():
        # Get summary info
        summary = row.get('summary', {})
        if isinstance(summary, dict):
            labels = summary.get('labels', [])
            labels_str = ", ".join(labels[:3]) if labels else ""
        else:
            labels_str = ""

        display_data.append({
            'Timestamp': row.get('timestamp', '').strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row.get('timestamp')) else '',
            'Alert ID': str(row.get('alert_id', ''))[:12],
            'Conversation': row.get('conversation_id', '')[:15],
            'Danger Level': row.get('danger_level', '').upper(),
            'Violations': row.get('violation_count', 0),
            'Window': f"{row.get('window_size_minutes', 5)} min",
            'Labels': labels_str
        })

    display_df = pd.DataFrame(display_data)

    # Pagination
    total_rows = len(display_df)
    total_pages = (total_rows - 1) // page_size + 1 if total_rows > 0 else 1

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        page = st.selectbox(
            "Page",
            options=range(1, total_pages + 1),
            format_func=lambda x: f"Page {x} of {total_pages}",
            key="alerts_page"
        )

    # Get page data
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_df = display_df.iloc[start_idx:end_idx]

    # Style the dataframe
    def style_danger(val):
        if val == 'HIGH':
            return f'background-color: {config.DANGER_COLORS["high"]}; color: white'
        elif val == 'MEDIUM':
            return f'background-color: {config.DANGER_COLORS["medium"]}; color: white'
        elif val == 'LOW':
            return f'background-color: {config.DANGER_COLORS["low"]}; color: white'
        return ''

    styled_df = page_df.style.applymap(
        style_danger,
        subset=['Danger Level']
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(f"Showing {start_idx + 1}-{min(end_idx, total_rows)} of {total_rows} alerts")
