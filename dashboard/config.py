"""Dashboard configuration settings"""

from dataclasses import dataclass, field
from typing import Dict, List
from pathlib import Path
import os


@dataclass
class DashboardConfig:
    """Configuration for Streamlit dashboard"""

    # Data paths
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")

    # Page settings
    PAGE_TITLE: str = "LLM Monitoring Dashboard"
    PAGE_ICON: str = ":shield:"
    LAYOUT: str = "wide"

    # Refresh settings
    DEFAULT_REFRESH_INTERVAL: int = 30
    REFRESH_INTERVALS: List[int] = field(default_factory=lambda: [5, 10, 30, 60, 120, 300])

    # Table settings
    DEFAULT_PAGE_SIZE: int = 20
    MAX_TEXT_LENGTH: int = 80

    # Chart settings
    CHART_HEIGHT: int = 350

    # Toxicity labels
    TOXICITY_LABELS: List[str] = field(default_factory=lambda: [
        "toxicity",
        "severe_toxicity",
        "obscene",
        "threat",
        "insult",
        "identity_attack"
    ])

    # Severity levels
    SEVERITY_LEVELS: List[str] = field(default_factory=lambda: ["low", "medium", "high"])

    # Danger levels
    DANGER_LEVELS: List[str] = field(default_factory=lambda: ["low", "medium", "high"])

    # Color schemes
    SEVERITY_COLORS: Dict[str, str] = field(default_factory=lambda: {
        "low": "#4CAF50",      # Green
        "medium": "#FF9800",   # Orange
        "high": "#F44336"      # Red
    })

    DANGER_COLORS: Dict[str, str] = field(default_factory=lambda: {
        "low": "#4CAF50",
        "medium": "#FF9800",
        "high": "#F44336"
    })

    TOXICITY_LABEL_COLORS: Dict[str, str] = field(default_factory=lambda: {
        "toxicity": "#E91E63",
        "severe_toxicity": "#9C27B0",
        "obscene": "#673AB7",
        "threat": "#F44336",
        "insult": "#FF5722",
        "identity_attack": "#795548"
    })

    @property
    def output_path(self) -> Path:
        return Path(self.OUTPUT_DIR)


# Global config instance
config = DashboardConfig()
