import json
from pathlib import Path
from loguru import logger
from src.config import KafkaInputConfig
from src.kafka.conversation_consumer import ConversationConsumer
from src.processors.guardrail_processor import GuardrailProcessor
from src.kafka.violation_producer import ViolationProducer


class GuardrailInputProcessor:
    """
    Kafka-based input processor for LLM conversations

    Consumes user messages from Kafka topic, processes them through
    guardrails before they reach the LLM, and publishes violations.
    """

    def __init__(self, config: KafkaInputConfig):
        """
        Initialize the input processor

        Args:
            config: KafkaInputConfig with Kafka and processing settings
        """
        self.config = config

        # Initialize Kafka consumer for conversations
        self.consumer = ConversationConsumer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            topic=config.KAFKA_INPUT_TOPIC,
            consumer_group=config.KAFKA_INPUT_CONSUMER_GROUP,
            enabled=True
        )

        # Initialize guardrail processor
        self.processor = GuardrailProcessor(threshold=config.TOXICITY_THRESHOLD)

        # Initialize Kafka producer for violations
        self.producer = ViolationProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            topic=config.KAFKA_OUTPUT_TOPIC,
            enabled=True
        )

        # Create output directory for backup file
        output_path = Path(config.KAFKA_INPUT_OUTPUT_FILE)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            'conversations_processed': 0,
            'violations_detected': 0,
            'violations_by_severity': {'low': 0, 'medium': 0, 'high': 0}
        }

    def run(self):
        """Main processing loop - consumes conversations and processes them"""
        logger.info("=" * 60)
        logger.info("Starting Guardrail Input Processor")
        logger.info(f"Input Topic: {self.config.KAFKA_INPUT_TOPIC}")
        logger.info(f"Output Topic: {self.config.KAFKA_OUTPUT_TOPIC}")
        logger.info(f"Toxicity Threshold: {self.config.TOXICITY_THRESHOLD}")
        logger.info(f"Backup Output: {self.config.KAFKA_INPUT_OUTPUT_FILE}")
        logger.info("=" * 60)

        try:
            with open(self.config.KAFKA_INPUT_OUTPUT_FILE, 'a') as backup_file:
                for conversation in self.consumer.consume_conversations():
                    self._process_conversation(conversation, backup_file)

        except KeyboardInterrupt:
            self._log_shutdown_stats()
        except Exception as e:
            logger.error(f"Error in processing loop: {e}")
            raise
        finally:
            self.consumer.close()
            self.producer.close()

    def _process_conversation(self, conversation, backup_file):
        """
        Process a single conversation

        Args:
            conversation: Conversation object from Kafka
            backup_file: Open file handle for backup output
        """
        self.stats['conversations_processed'] += 1

        # Process through guardrails
        violation = self.processor.process_conversation(conversation)

        if violation:
            self.stats['violations_detected'] += 1
            self.stats['violations_by_severity'][violation.severity.value] += 1

            # Log to console
            logger.warning(
                f"[{violation.severity.value.upper()}] "
                f"Violation in {violation.conversation_id} | "
                f"Labels: {', '.join(violation.toxicity_labels)}"
            )

            # Write to backup file
            backup_file.write(json.dumps(violation.to_dict()) + '\n')
            backup_file.flush()

            # Send to Kafka
            self.producer.send_violation(violation)
        else:
            logger.debug(f"Conversation {conversation.conversation_id}: Clean")

    def _log_shutdown_stats(self):
        """Log statistics on shutdown"""
        logger.info("\n" + "=" * 60)
        logger.info("Shutting down Guardrail Input Processor...")
        logger.info(f"Conversations processed: {self.stats['conversations_processed']}")
        logger.info(f"Violations detected: {self.stats['violations_detected']}")
        logger.info(f"  LOW: {self.stats['violations_by_severity']['low']}")
        logger.info(f"  MEDIUM: {self.stats['violations_by_severity']['medium']}")
        logger.info(f"  HIGH: {self.stats['violations_by_severity']['high']}")
        logger.info("Consumer stats: " + str(self.consumer.get_stats()))
        logger.info("Producer stats: " + str(self.producer.get_stats()))
        logger.info("=" * 60)


def main():
    """Entry point for guardrail input processor service"""
    config = KafkaInputConfig()
    service = GuardrailInputProcessor(config)
    service.run()


if __name__ == "__main__":
    main()
