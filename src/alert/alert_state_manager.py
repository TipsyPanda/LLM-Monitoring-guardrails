import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from loguru import logger

from src.models.alert import Alert, AlertStatus, DangerLevel


class AlertStateManager:
    """
    Manages alert state lifecycle: creation, updates, expiration, and persistence.

    Key Responsibilities:
    - Load existing alerts from JSONL on initialization
    - Maintain in-memory index of active alerts by conversation_id
    - Handle alert updates (increment count, update score)
    - Expire stale alerts (mark as inactive after window duration)
    - Persist state changes atomically to JSONL

    Design:
    - Full file rewrite strategy with atomic rename for data integrity
    - Active alerts tracked in-memory for O(1) lookups
    - Both active and inactive alerts persisted to JSONL
    """

    def __init__(self, alerts_file: str, window_size_seconds: int):
        self.alerts_file = Path(alerts_file)
        self.window_size_seconds = window_size_seconds

        # In-memory index: conversation_id -> Alert
        self.active_alerts: Dict[str, Alert] = {}

        # Load existing state from file
        self._load_state()

        logger.info(
            f"AlertStateManager initialized | "
            f"file={self.alerts_file} "
            f"window={window_size_seconds}s "
            f"active_alerts={len(self.active_alerts)}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_active_alert(self, conversation_id: str) -> Optional[Alert]:
        """
        Check if conversation has an active alert.

        Returns:
            Alert if active alert exists, None otherwise
        """
        return self.active_alerts.get(conversation_id)

    def create_alert(self, alert: Alert) -> Alert:
        """
        Create new alert and persist to file.

        Args:
            alert: Alert instance to create

        Returns:
            The created alert
        """
        alert.status = AlertStatus.ACTIVE
        self.active_alerts[alert.conversation_id] = alert

        logger.info(
            f"[ALERT CREATED] conversation={alert.conversation_id} "
            f"level={alert.danger_level.value} "
            f"count={alert.violation_count} "
            f"score={alert.window_score:.3f}"
        )

        self._persist_state()
        return alert

    def update_alert(
        self,
        conversation_id: str,
        violations: List[dict],
        window_score: float,
        danger_level: DangerLevel,
    ) -> Alert:
        """
        Update existing alert with new violation data.

        Args:
            conversation_id: Conversation ID to update
            violations: Current window violations
            window_score: Recalculated window score
            danger_level: Recalculated danger level

        Returns:
            Updated alert

        Raises:
            KeyError: If no active alert exists for conversation_id
        """
        if conversation_id not in self.active_alerts:
            raise KeyError(
                f"No active alert for conversation_id={conversation_id}"
            )

        alert = self.active_alerts[conversation_id]

        # Update alert fields
        alert.violation_count = len(violations)
        alert.window_score = window_score
        alert.danger_level = danger_level
        alert.last_updated = datetime.now(timezone.utc)

        # Update summary (aggregate labels)
        alert.summary = self._build_summary(violations)

        logger.info(
            f"[ALERT UPDATED] conversation={conversation_id} "
            f"level={danger_level.value} "
            f"count={alert.violation_count} "
            f"score={alert.window_score:.3f}"
        )

        self._persist_state()
        return alert

    def expire_stale_alerts(self) -> List[str]:
        """
        Mark alerts as inactive if they're beyond the time window.

        Returns:
            List of expired conversation IDs
        """
        now = datetime.now(timezone.utc)
        expired_conv_ids = []

        for conv_id, alert in list(self.active_alerts.items()):
            elapsed = (now - alert.last_updated).total_seconds()

            if elapsed > self.window_size_seconds:
                alert.status = AlertStatus.INACTIVE
                del self.active_alerts[conv_id]
                expired_conv_ids.append(conv_id)

                logger.info(
                    f"[ALERT EXPIRED] conversation={conv_id} "
                    f"elapsed={elapsed:.1f}s "
                    f"window={self.window_size_seconds}s"
                )

        if expired_conv_ids:
            self._persist_state()

        return expired_conv_ids

    # ------------------------------------------------------------------
    # State Management
    # ------------------------------------------------------------------

    def _load_state(self):
        """
        Load existing alerts from JSONL file.
        Populate active_alerts index with ACTIVE alerts.
        """
        if not self.alerts_file.exists():
            logger.info(f"No existing alerts file at {self.alerts_file}")
            return

        now = datetime.now(timezone.utc)
        total_loaded = 0
        active_loaded = 0

        try:
            with open(self.alerts_file, "r") as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        alert = Alert.from_dict(data)
                        total_loaded += 1

                        # Only track active alerts in memory
                        if alert.status == AlertStatus.ACTIVE:
                            # Validate alert hasn't expired
                            elapsed = (now - alert.last_updated).total_seconds()
                            if elapsed <= self.window_size_seconds:
                                self.active_alerts[alert.conversation_id] = alert
                                active_loaded += 1
                            else:
                                # Mark as inactive since it's expired
                                logger.debug(
                                    f"Loaded expired alert: {alert.conversation_id}, "
                                    f"marking inactive"
                                )
                                alert.status = AlertStatus.INACTIVE

                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.warning(
                            f"Failed to parse alert at line {line_num}: {e}"
                        )
                        continue

            logger.info(
                f"Loaded {total_loaded} alerts from file "
                f"({active_loaded} active, {total_loaded - active_loaded} inactive)"
            )

        except Exception as e:
            logger.error(f"Error loading alerts from {self.alerts_file}: {e}")

    def _persist_state(self):
        """
        Atomically write all alerts (active + inactive) to JSONL.

        Strategy:
        1. Read all existing alerts from file
        2. Update with current in-memory active alerts
        3. Write to temporary file
        4. Atomic rename to target file

        This ensures:
        - No partial writes (crash safety)
        - No lost data (both active and inactive preserved)
        - Atomic updates (readers see consistent state)
        """
        temp_file = self.alerts_file.with_suffix(".tmp")

        try:
            # 1. Read all existing alerts (to preserve inactive ones)
            all_alerts = self._read_all_alerts()

            # 2. Update with current active alerts
            for alert in self.active_alerts.values():
                all_alerts[alert.alert_id] = alert

            # 3. Write to temp file
            with open(temp_file, "w") as f:
                for alert in all_alerts.values():
                    f.write(json.dumps(alert.to_dict()) + "\n")

            # 4. Atomic rename (POSIX guarantees atomicity)
            temp_file.replace(self.alerts_file)

            logger.debug(
                f"Persisted {len(all_alerts)} alerts "
                f"({len(self.active_alerts)} active)"
            )

        except Exception as e:
            logger.error(f"Error persisting alerts: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    def _read_all_alerts(self) -> Dict[str, Alert]:
        """
        Read complete alert history from file.

        Returns:
            Dict mapping alert_id -> Alert
        """
        all_alerts = {}

        if not self.alerts_file.exists():
            return all_alerts

        try:
            with open(self.alerts_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        alert = Alert.from_dict(data)
                        all_alerts[alert.alert_id] = alert
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.warning(f"Failed to parse alert: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error reading alerts from {self.alerts_file}: {e}")

        return all_alerts

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(violations: List[dict]) -> dict:
        """Build summary metadata from violations"""
        labels = {
            label
            for v in violations
            for label in v.get("toxicity_labels", [])
        }

        return {
            "total_violations": len(violations),
            "labels": sorted(labels),
        }
