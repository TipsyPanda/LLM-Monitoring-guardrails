import json
from pathlib import Path
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from loguru import logger
from src.config import AlertConfig
from src.alert.window_tracker import SlidingWindowTracker
from src.alert.alert_generator import AlertGenerator


class AlertConsumerService:
    """
    Kafka consumer service that monitors violations and generates danger alerts

    Consumes violations from Kafka topic, tracks them in sliding windows,
    and generates alerts based on violation patterns over time.
    """

    def __init__(self, config: AlertConfig):
        """
        Initialize the alert consumer service

        Args:
            config: AlertConfig with Kafka and alert settings
        """
        self.config = config

        # Initialize Kafka consumer
        try:
            self.consumer = KafkaConsumer(
                config.KAFKA_TOPIC,
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS.split(','),
                group_id=config.ALERT_CONSUMER_GROUP,
                auto_offset_reset='earliest',  # Process all messages from beginning
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            logger.info(f"Kafka consumer initialized: {config.KAFKA_BOOTSTRAP_SERVERS}, topic: {config.KAFKA_TOPIC}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            raise

        # Initialize window tracker and alert generator
        self.window_tracker = SlidingWindowTracker(
            window_size_seconds=config.ALERT_WINDOW_SIZE_SECONDS
        )
        self.alert_generator = AlertGenerator(
            window_size_minutes=config.ALERT_WINDOW_SIZE_SECONDS // 60
        )

        # Create output directory
        output_path = Path(config.ALERT_OUTPUT_FILE)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            'violations_processed': 0,
            'alerts_generated': 0,
            'alerts_by_level': {'low': 0, 'medium': 0, 'high': 0}
        }

    def run(self):
        """Main consumer loop - processes violations and generates alerts"""
        logger.info("="*60)
        logger.info("Starting Alert Consumer Service")
        logger.info(f"Kafka Topic: {self.config.KAFKA_TOPIC}")
        logger.info(f"Window Size: {self.config.ALERT_WINDOW_SIZE_SECONDS}s ({self.config.ALERT_WINDOW_SIZE_SECONDS // 60} minutes)")
        logger.info(f"Alert Output: {self.config.ALERT_OUTPUT_FILE}")
        logger.info("="*60)

        try:
            with open(self.config.ALERT_OUTPUT_FILE, 'a') as alert_file:
                for message in self.consumer:
                    self.process_violation(message.value, alert_file)

        except KeyboardInterrupt:
            logger.info("\n" + "="*60)
            logger.info("Shutting down Alert Consumer Service...")
            logger.info(f"Violations processed: {self.stats['violations_processed']}")
            logger.info(f"Alerts generated: {self.stats['alerts_generated']}")
            logger.info(f"  LOW: {self.stats['alerts_by_level']['low']}")
            logger.info(f"  MEDIUM: {self.stats['alerts_by_level']['medium']}")
            logger.info(f"  HIGH: {self.stats['alerts_by_level']['high']}")
            logger.info("="*60)
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
            raise
        finally:
            self.consumer.close()

    def process_violation(self, violation: dict, alert_file):
        """
        Process incoming violation and generate alert

        Args:
            violation: Violation dictionary from Kafka
            alert_file: Open file handle for writing alerts
        """
        self.stats['violations_processed'] += 1
        conv_id = violation['conversation_id']

        # Add to window and get current count
        count = self.window_tracker.add_violation(violation)

        # Get all violations in current window
        violations = self.window_tracker.get_violations(conv_id)

        # Generate alert
        alert = self.alert_generator.generate_alert(conv_id, count, violations)

        # Update stats
        self.stats['alerts_generated'] += 1
        self.stats['alerts_by_level'][alert.danger_level.value] += 1

        # Output alert to console and file
        self._output_alert_console(alert)
        self._output_alert_file(alert, alert_file)

    def _output_alert_console(self, alert):
        """
        Output alert to console with color formatting

        Args:
            alert: Alert object
        """
        # Color codes for danger levels
        colors = {
            'low': '\033[92m',      # Green
            'medium': '\033[93m',   # Yellow
            'high': '\033[91m'      # Red
        }
        reset = '\033[0m'

        danger_color = colors.get(alert.danger_level.value, '')
        danger_text = f"{danger_color}[{alert.danger_level.value.upper()} DANGER]{reset}"

        logger.warning(
            f"{danger_text} Conversation {alert.conversation_id}\n"
            f"  - Violations in last {alert.window_size_minutes} min: {alert.violation_count}\n"
            f"  - Severities: {', '.join(alert.summary['severities'])}\n"
            f"  - Labels: {', '.join(alert.summary['labels'])}"
        )

    def _output_alert_file(self, alert, alert_file):
        """
        Output alert to JSONL file

        Args:
            alert: Alert object
            alert_file: Open file handle
        """
        alert_file.write(json.dumps(alert.to_dict()) + '\n')
        alert_file.flush()


def main():
    """Entry point for alert consumer service"""
    config = AlertConfig()
    service = AlertConsumerService(config)
    service.run()


if __name__ == "__main__":
    main()
