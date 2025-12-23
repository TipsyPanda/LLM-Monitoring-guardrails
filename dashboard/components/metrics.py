"""KPI metric cards component"""

import streamlit as st
import pandas as pd
from typing import Optional

from dashboard.data.processor import DataProcessor


def render_metric_cards(
    violations_df: pd.DataFrame,
    alerts_df: pd.DataFrame,
    previous_violations_df: Optional[pd.DataFrame] = None
):
    """
    Render top-level KPI metric cards

    Args:
        violations_df: Current violations DataFrame
        alerts_df: Current alerts DataFrame
        previous_violations_df: Previous period violations for delta calculation
    """
    col1, col2, col3, col4, col5 = st.columns(5)

    # Total Violations
    total_violations = len(violations_df)
    delta_violations = None
    if previous_violations_df is not None:
        delta_violations = total_violations - len(previous_violations_df)

    with col1:
        st.metric(
            label="Total Violations",
            value=total_violations,
            delta=delta_violations
        )

    # Total Alerts
    total_alerts = len(alerts_df)
    with col2:
        st.metric(
            label="Total Alerts",
            value=total_alerts
        )

    # High Severity Violations
    high_severity = 0
    if not violations_df.empty and 'severity' in violations_df.columns:
        high_severity = len(violations_df[violations_df['severity'] == 'high'])

    with col3:
        st.metric(
            label="High Severity",
            value=high_severity,
            delta=None,
            delta_color="inverse"
        )

    # Medium Severity Violations
    medium_severity = 0
    if not violations_df.empty and 'severity' in violations_df.columns:
        medium_severity = len(violations_df[violations_df['severity'] == 'medium'])

    with col4:
        st.metric(
            label="Medium Severity",
            value=medium_severity
        )

    # Low Severity Violations
    low_severity = 0
    if not violations_df.empty and 'severity' in violations_df.columns:
        low_severity = len(violations_df[violations_df['severity'] == 'low'])

    with col5:
        st.metric(
            label="Low Severity",
            value=low_severity
        )


def render_alert_metrics(alerts_df: pd.DataFrame):
    """
    Render alert-specific metrics

    Args:
        alerts_df: Alerts DataFrame
    """
    col1, col2, col3 = st.columns(3)

    # High Danger Alerts
    high_danger = 0
    if not alerts_df.empty and 'danger_level' in alerts_df.columns:
        high_danger = len(alerts_df[alerts_df['danger_level'] == 'high'])

    with col1:
        st.metric(
            label="High Danger Alerts",
            value=high_danger,
            delta_color="inverse"
        )

    # Medium Danger Alerts
    medium_danger = 0
    if not alerts_df.empty and 'danger_level' in alerts_df.columns:
        medium_danger = len(alerts_df[alerts_df['danger_level'] == 'medium'])

    with col2:
        st.metric(
            label="Medium Danger",
            value=medium_danger
        )

    # Low Danger Alerts
    low_danger = 0
    if not alerts_df.empty and 'danger_level' in alerts_df.columns:
        low_danger = len(alerts_df[alerts_df['danger_level'] == 'low'])

    with col3:
        st.metric(
            label="Low Danger",
            value=low_danger
        )
