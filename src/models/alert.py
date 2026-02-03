from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Dict, Optional, List
from enum import Enum


class DangerLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass
class Alert:
    """
    Alert generated when policy thresholds are exceeded
    within a sliding window.

    timestamp     = event-time (first seen, earliest violation in window)
    last_updated  = most recent violation update time
    generated_at  = processing-time (alert emission)
    status        = active (within window) or inactive (expired)
    """

    alert_id: str
    conversation_id: str

    danger_level: DangerLevel

    # 🔥 NEW: aggregated policy signal
    window_score: float

    violation_count: int
    window_size_minutes: int

    # ⏱️ EVENT TIME (earliest violation in window / first seen)
    timestamp: datetime

    # ⏱️ PROCESSING TIME (Kafka / consumer time)
    generated_at: Optional[datetime] = None

    # 🔄 STATE MANAGEMENT
    status: AlertStatus = AlertStatus.ACTIVE
    last_updated: Optional[datetime] = None

    summary: Dict = field(default_factory=dict)

    def __post_init__(self):
        # Ensure processing time always exists
        if self.generated_at is None:
            self.generated_at = datetime.now(timezone.utc)

        # Initialize last_updated to timestamp (first seen) if not provided
        if self.last_updated is None:
            self.last_updated = self.timestamp

    def to_dict(self):
        data = asdict(self)

        data["timestamp"] = self.timestamp.isoformat()
        data["generated_at"] = self.generated_at.isoformat()
        data["last_updated"] = self.last_updated.isoformat()
        data["danger_level"] = self.danger_level.value
        data["status"] = self.status.value

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Alert":
        """Create Alert instance from dictionary (for loading from JSONL)"""
        # Parse enums
        data["danger_level"] = DangerLevel(data["danger_level"])
        data["status"] = AlertStatus(data.get("status", "active"))

        # Parse timestamps
        data["timestamp"] = cls._parse_timestamp(data["timestamp"])
        data["generated_at"] = cls._parse_timestamp(data["generated_at"])

        if "last_updated" in data and data["last_updated"]:
            data["last_updated"] = cls._parse_timestamp(data["last_updated"])

        return cls(**data)

    def update_from_violations(self, violations: List[dict], new_window_score: float):
        """Update alert when new violations arrive"""
        self.violation_count = len(violations)
        self.window_score = new_window_score
        self.last_updated = datetime.now(timezone.utc)

    @staticmethod
    def _parse_timestamp(ts) -> datetime:
        """Parse timestamp from string or datetime object"""
        if isinstance(ts, datetime):
            return ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(
                tzinfo=timezone.utc
            )

        parsed = datetime.fromisoformat(ts)
        return (
            parsed.astimezone(timezone.utc)
            if parsed.tzinfo
            else parsed.replace(tzinfo=timezone.utc)
        )
