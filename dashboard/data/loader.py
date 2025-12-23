"""Data loading utilities for the dashboard"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import streamlit as st

from dashboard.config import config


class DataLoader:
    """Load and cache JSONL data files"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or config.OUTPUT_DIR)

    @st.cache_data(ttl=5)
    def load_violations(_self, source: str = "both") -> pd.DataFrame:
        """
        Load violations from JSONL files

        Args:
            source: "batch" | "kafka" | "both"

        Returns:
            DataFrame with violation records
        """
        files = []
        if source in ("batch", "both"):
            files.append(_self.output_dir / "violations.jsonl")
        if source in ("kafka", "both"):
            files.append(_self.output_dir / "kafka_violations.jsonl")

        records = []
        for file_path in files:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                records.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        return df

    @st.cache_data(ttl=5)
    def load_alerts(_self) -> pd.DataFrame:
        """
        Load alerts from JSONL file

        Returns:
            DataFrame with alert records
        """
        alerts_file = _self.output_dir / "alerts.jsonl"

        if not alerts_file.exists():
            return pd.DataFrame()

        records = []
        with open(alerts_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        return df

    def get_file_stats(self) -> Dict[str, Dict]:
        """
        Get file modification times and sizes

        Returns:
            Dictionary with file stats
        """
        stats = {}
        file_names = ["violations.jsonl", "kafka_violations.jsonl", "alerts.jsonl"]

        for name in file_names:
            path = self.output_dir / name
            if path.exists():
                stat = path.stat()
                stats[name] = {
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "size": stat.st_size,
                    "exists": True
                }
            else:
                stats[name] = {
                    "modified": None,
                    "size": 0,
                    "exists": False
                }

        return stats

    def count_lines(self, filename: str) -> int:
        """Count lines in a JSONL file"""
        path = self.output_dir / filename
        if not path.exists():
            return 0

        count = 0
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    count += 1
        return count
