"""Data processing and transformation utilities"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

from dashboard.config import config


class DataProcessor:
    """Transform and aggregate data for visualization"""

    @staticmethod
    def filter_data(
        df: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severities: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        min_score: float = 0.0,
        **kwargs
    ) -> pd.DataFrame:
        """
        Apply filters to violations DataFrame

        Args:
            df: Input DataFrame
            start_date: Filter start date
            end_date: Filter end date
            severities: List of severity levels to include
            labels: List of toxicity labels to include
            conversation_id: Filter by conversation ID (partial match)
            min_score: Minimum toxicity score threshold

        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df

        filtered = df.copy()

        if start_date and 'timestamp' in filtered.columns:
            filtered = filtered[filtered['timestamp'] >= pd.to_datetime(start_date)]

        if end_date and 'timestamp' in filtered.columns:
            filtered = filtered[filtered['timestamp'] <= pd.to_datetime(end_date)]

        if severities and 'severity' in filtered.columns:
            filtered = filtered[filtered['severity'].isin(severities)]

        if labels and 'toxicity_labels' in filtered.columns:
            filtered = filtered[
                filtered['toxicity_labels'].apply(
                    lambda x: any(label in x for label in labels) if isinstance(x, list) else False
                )
            ]

        if conversation_id and 'conversation_id' in filtered.columns:
            filtered = filtered[
                filtered['conversation_id'].str.contains(conversation_id, case=False, na=False)
            ]

        if min_score > 0 and 'metadata' in filtered.columns:
            filtered = filtered[
                filtered['metadata'].apply(
                    lambda x: max(x.get('scores', {}).values(), default=0) >= min_score
                    if isinstance(x, dict) else False
                )
            ]

        return filtered

    @staticmethod
    def aggregate_by_time(
        df: pd.DataFrame,
        freq: str = 'H',
        value_column: str = 'severity'
    ) -> pd.DataFrame:
        """
        Aggregate data by time period

        Args:
            df: Input DataFrame with timestamp column
            freq: Frequency string ('H' for hourly, 'D' for daily)
            value_column: Column to group by (severity or danger_level)

        Returns:
            Aggregated DataFrame with period, value, and count columns
        """
        if df.empty or 'timestamp' not in df.columns:
            return pd.DataFrame(columns=['period', value_column, 'count'])

        df_copy = df.copy()
        df_copy['period'] = df_copy['timestamp'].dt.floor(freq)

        if value_column in df_copy.columns:
            agg = df_copy.groupby(['period', value_column]).size().reset_index(name='count')
        else:
            agg = df_copy.groupby('period').size().reset_index(name='count')

        return agg

    @staticmethod
    def get_label_counts(df: pd.DataFrame) -> Dict[str, int]:
        """
        Count occurrences of each toxicity label

        Args:
            df: Input DataFrame with toxicity_labels column

        Returns:
            Dictionary of label counts
        """
        counts = {label: 0 for label in config.TOXICITY_LABELS}

        if df.empty or 'toxicity_labels' not in df.columns:
            return counts

        for labels in df['toxicity_labels']:
            if isinstance(labels, list):
                for label in labels:
                    if label in counts:
                        counts[label] += 1

        return counts

    @staticmethod
    def get_severity_distribution(df: pd.DataFrame) -> Dict[str, int]:
        """
        Get count of each severity level

        Args:
            df: Input DataFrame with severity column

        Returns:
            Dictionary of severity counts
        """
        distribution = {level: 0 for level in config.SEVERITY_LEVELS}

        if df.empty or 'severity' not in df.columns:
            return distribution

        counts = df['severity'].value_counts().to_dict()
        distribution.update(counts)

        return distribution

    @staticmethod
    def get_danger_distribution(df: pd.DataFrame) -> Dict[str, int]:
        """
        Get count of each danger level

        Args:
            df: Input DataFrame with danger_level column

        Returns:
            Dictionary of danger level counts
        """
        distribution = {level: 0 for level in config.DANGER_LEVELS}

        if df.empty or 'danger_level' not in df.columns:
            return distribution

        counts = df['danger_level'].value_counts().to_dict()
        distribution.update(counts)

        return distribution

    @staticmethod
    def extract_scores(df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract toxicity scores into flat columns

        Args:
            df: Input DataFrame with metadata column

        Returns:
            DataFrame with individual score columns
        """
        if df.empty or 'metadata' not in df.columns:
            return pd.DataFrame()

        records = []
        for _, row in df.iterrows():
            metadata = row.get('metadata', {})
            scores = metadata.get('scores', {}) if isinstance(metadata, dict) else {}

            record = {
                'conversation_id': row.get('conversation_id', ''),
                'timestamp': row.get('timestamp'),
                'severity': row.get('severity', ''),
            }
            for label in config.TOXICITY_LABELS:
                record[label] = scores.get(label, 0.0)

            records.append(record)

        return pd.DataFrame(records)

    @staticmethod
    def get_top_score(metadata: dict) -> float:
        """Get the highest toxicity score from metadata"""
        if not isinstance(metadata, dict):
            return 0.0
        scores = metadata.get('scores', {})
        if not scores:
            return 0.0
        return max(scores.values())

    @staticmethod
    def truncate_text(text: str, max_length: int = 80) -> str:
        """Truncate text with ellipsis"""
        if not isinstance(text, str):
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
