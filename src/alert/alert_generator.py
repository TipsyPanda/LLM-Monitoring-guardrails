from datetime import datetime
from typing import List
from src.models.alert import Alert, DangerLevel
from loguru import logger


class AlertGenerator:
    """
    Generate danger alerts based on violation counts in sliding windows

    Danger levels:
    - LOW: 1 violation in window
    - MEDIUM: 2 violations in window
    - HIGH: 3+ violations in window
    """

    def __init__(self, window_size_minutes: int = 5):
        """
        Initialize the alert generator

        Args:
            window_size_minutes: Size of the sliding window in minutes
        """
        self.window_size_minutes = window_size_minutes
        logger.info(f"AlertGenerator initialized with {window_size_minutes}-minute window")

    def calculate_danger_level(self, violation_count: int) -> DangerLevel:
        """
        Calculate danger level based on violation count

        Args:
            violation_count: Number of violations in the window

        Returns:
            DangerLevel enum (LOW, MEDIUM, or HIGH)
        """
        if violation_count >= 3:
            return DangerLevel.HIGH
        elif violation_count == 2:
            return DangerLevel.MEDIUM
        else:
            return DangerLevel.LOW

    def generate_alert(self, conversation_id: str, violation_count: int, violations: List[dict]) -> Alert:
        """
        Generate an alert with full context

        Args:
            conversation_id: ID of the conversation
            violation_count: Number of violations in the window
            violations: List of violation dictionaries

        Returns:
            Alert object with all details
        """
        danger_level = self.calculate_danger_level(violation_count)

        # Generate unique alert ID
        alert_id = f"alert_{conversation_id}_{int(datetime.now().timestamp())}"

        # Extract summary information
        severities = [v['severity'] for v in violations]
        unique_labels = list(set(
            label
            for v in violations
            for label in v['toxicity_labels']
        ))

        summary = {
            'severities': severities,
            'labels': unique_labels,
            'severity_counts': {
                'low': severities.count('low'),
                'medium': severities.count('medium'),
                'high': severities.count('high')
            }
        }

        alert = Alert(
            alert_id=alert_id,
            conversation_id=conversation_id,
            danger_level=danger_level,
            violation_count=violation_count,
            window_size_minutes=self.window_size_minutes,
            timestamp=datetime.now(),
            violations=violations,
            summary=summary
        )

        logger.debug(
            f"Generated {danger_level.value.upper()} alert for {conversation_id}: "
            f"{violation_count} violations"
        )

        return alert
