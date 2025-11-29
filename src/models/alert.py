from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict
from enum import Enum


class DangerLevel(Enum):
    """Danger level classification based on violation count in window"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Alert:
    """
    Alert generated when violations exceed thresholds in a time window

    Danger levels:
    - LOW: 1 violation in 5-minute window
    - MEDIUM: 2 violations in 5-minute window
    - HIGH: 3+ violations in 5-minute window
    """
    alert_id: str
    conversation_id: str
    danger_level: DangerLevel
    violation_count: int
    window_size_minutes: int
    timestamp: datetime
    violations: List[dict]
    summary: Dict

    def to_dict(self):
        """Convert alert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['danger_level'] = self.danger_level.value
        return data
