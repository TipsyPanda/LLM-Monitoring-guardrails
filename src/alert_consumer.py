import json
from pathlib import Path
from kafka import KafkaConsumer
from loguru import logger
from datetime import datetime, timezone

from src.config import AlertConfig
from src.alert.window_tracker import SlidingWindowTracker
from src.alert.alert_generator import AlertGenerator
from src.alert.alert_state_manager import AlertStateManager


class AlertConsumerService:
    """
    Kafka consumer service that aggregates violations and generates alerts.

    Core principle:
    - Sliding window accumulates violations
    - AlertGenerator is the ONLY policy decision engine
    - AlertStateManager maintains alert lifecycle (create, update, expire)
    - Alerts persist as "active" until they expire beyond time window
    """

    def __init__(self, config: AlertConfig):
        self.config = config

        self.consumer = KafkaConsumer(
            config.TOPIC,
            bootstrap_servers=config.BOOTSTRAP_SERVERS.split(","),
            group_id=config.CONSUMER_GROUP,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )

        self.window_tracker = SlidingWindowTracker(
            window_size_seconds=config.WINDOW_SIZE_SECONDS
        )

        self.alert_generator = AlertGenerator(
            window_size_minutes=config.WINDOW_SIZE_SECONDS // 60,
            low_threshold=config.LOW_THRESHOLD,
            medium_threshold=config.MEDIUM_THRESHOLD,
            high_threshold=config.HIGH_THRESHOLD,
        )

        # NEW: Alert state manager
        output_path = Path(config.OUTPUT_FILE)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.alert_state_manager = AlertStateManager(
            alerts_file=config.OUTPUT_FILE,
            window_size_seconds=config.WINDOW_SIZE_SECONDS,
        )

        # Periodic cleanup tracking
        self.last_cleanup = datetime.now(timezone.utc)
        self.cleanup_interval_seconds = 60  # Check for expired alerts every 60s

        self.stats = {
            "violations_processed": 0,
            "alerts_generated": 0,
            "alerts_updated": 0,
            "alerts_expired": 0,
            "alerts_by_level": {"low": 0, "medium": 0, "high": 0},
        }

        logger.info(
            "AlertConsumer initialized | "
            f"topic={config.TOPIC} "
            f"window={config.WINDOW_SIZE_SECONDS}s "
            f"thresholds=low:{config.LOW_THRESHOLD}, "
            f"medium:{config.MEDIUM_THRESHOLD}, "
            f"high:{config.HIGH_THRESHOLD}"
        )

    # ------------------------------------------------------------------

    def run(self):
        logger.info("=" * 60)
        logger.info("Starting Alert Consumer Service")
        logger.info("=" * 60)

        try:
            for message in self.consumer:
                self.process_violation(message.value)

        except KeyboardInterrupt:
            logger.warning("Shutdown requested by user")
        finally:
            self._log_shutdown()
            self.consumer.close()

    # ------------------------------------------------------------------

    def process_violation(self, violation: dict):
        self.stats["violations_processed"] += 1

        conv_id = violation["conversation_id"]
        score = violation.get("weighted_score")

        logger.debug(
            f"[Consumer] received violation "
            f"conversation={conv_id} "
            f"score={score}"
        )

        # 1️⃣ Add violation to sliding window
        count = self.window_tracker.add_violation(violation)

        logger.debug(
            f"[Consumer] window updated "
            f"conversation={conv_id} "
            f"count={count} "
            f"window_score={self.window_tracker.get_window_score(conv_id):.4f}"
        )

        # 2️⃣ Get current window violations and score
        violations = self.window_tracker.get_violations(conv_id)
        window_score = self.window_tracker.get_window_score(conv_id)

        # 3️⃣ Check for existing active alert
        existing_alert = self.alert_state_manager.get_active_alert(conv_id)

        if existing_alert:
            # UPDATE existing alert with new violations
            danger_level = self.alert_generator.reclassify_danger_level(window_score)

            if danger_level is not None:
                updated_alert = self.alert_state_manager.update_alert(
                    conversation_id=conv_id,
                    violations=violations,
                    window_score=window_score,
                    danger_level=danger_level,
                )
                self.stats["alerts_updated"] += 1
                self._output_alert_console(updated_alert)
            else:
                logger.debug(
                    f"[Consumer] alert exists but score below threshold "
                    f"conversation={conv_id} score={window_score:.4f}"
                )
        else:
            # NEW alert evaluation
            alert = self.alert_generator.generate_alert(
                conversation_id=conv_id,
                violations=violations,
            )

            if alert:
                # CREATE new alert
                self.alert_state_manager.create_alert(alert)
                self.stats["alerts_generated"] += 1
                self.stats["alerts_by_level"][alert.danger_level.value] += 1
                self._output_alert_console(alert)
            else:
                logger.debug(
                    f"[Consumer] no alert "
                    f"conversation={conv_id} "
                    f"window_size={len(violations)}"
                )

        # 4️⃣ Periodic cleanup of expired alerts
        self._maybe_expire_alerts()

    # ------------------------------------------------------------------

    def _maybe_expire_alerts(self):
        """
        Periodically check and expire stale alerts.
        Called after each violation is processed.
        """
        now = datetime.now(timezone.utc)
        elapsed = (now - self.last_cleanup).total_seconds()

        if elapsed >= self.cleanup_interval_seconds:
            expired = self.alert_state_manager.expire_stale_alerts()
            if expired:
                self.stats["alerts_expired"] += len(expired)
                logger.info(
                    f"[ALERTS EXPIRED] count={len(expired)} "
                    f"conversations={expired}"
                )
            self.last_cleanup = now

    # ------------------------------------------------------------------

    def _output_alert_console(self, alert):
        colors = {
            "low": "\033[92m",
            "medium": "\033[93m",
            "high": "\033[91m",
        }
        reset = "\033[0m"

        level = alert.danger_level.value
        color = colors.get(level, "")

        logger.warning(
            f"{color}[{level.upper()} ALERT]{reset} "
            f"conversation={alert.conversation_id}\n"
            f"  window_score={alert.window_score:.3f}\n"
            f"  violations={alert.violation_count}\n"
            f"  labels={', '.join(alert.summary.get('labels', []))}"
        )

    # ------------------------------------------------------------------

    def _log_shutdown(self):
        logger.info("=" * 60)
        logger.info("Shutting down Alert Consumer Service")
        logger.info(f"Violations processed: {self.stats['violations_processed']}")
        logger.info(f"Alerts generated: {self.stats['alerts_generated']}")
        logger.info(f"Alerts updated: {self.stats['alerts_updated']}")
        logger.info(f"Alerts expired: {self.stats['alerts_expired']}")
        logger.info(f"Alerts by level: {self.stats['alerts_by_level']}")
        logger.info("=" * 60)


def main():
    config = AlertConfig()
    service = AlertConsumerService(config)
    service.run()


if __name__ == "__main__":
    main()
