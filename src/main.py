import json
from pathlib import Path
from src.config import Config
from src.processors.dataset_loader import DatasetLoader
from src.processors.guardrail_processor import GuardrailProcessor
from src.kafka.violation_producer import ViolationProducer
from loguru import logger

def main():
    # Load configuration
    config = Config()

    # Initialize components
    loader = DatasetLoader(config.DATASET_PATH)
    processor = GuardrailProcessor(threshold=config.TOXICITY_THRESHOLD)
    producer = ViolationProducer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        topic=config.KAFKA_TOPIC,
        enabled=config.KAFKA_ENABLED
    )

    # Create output directory
    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "violations.jsonl"

    # Statistics
    stats = {
        'total_conversations': 0,
        'total_violations': 0,
        'severity_counts': {'low': 0, 'medium': 0, 'high': 0},
        'kafka_sent': 0,
        'kafka_failed': 0
    }

    # Process conversations
    logger.info("Starting conversation processing...")

    try:
        with open(output_file, 'w') as f:
            for conversation in loader.load_conversations():
                stats['total_conversations'] += 1

                violation = processor.process_conversation(conversation)

                if violation:
                    stats['total_violations'] += 1
                    stats['severity_counts'][violation.severity.value] += 1

                    # Console output
                    logger.warning(
                        f"[{violation.severity.value.upper()}] "
                        f"Violation in {violation.conversation_id} | "
                        f"Labels: {', '.join(violation.toxicity_labels)}"
                    )

                    # File output (backup)
                    f.write(json.dumps(violation.to_dict()) + '\n')

                    # Kafka output
                    if producer.send_violation(violation):
                        stats['kafka_sent'] += 1
                    else:
                        stats['kafka_failed'] += 1
    finally:
        # Ensure Kafka producer is closed
        producer.close()

    # Summary
    logger.info("\n" + "="*50)
    logger.info("Processing Complete!")
    logger.info(f"Total conversations: {stats['total_conversations']}")
    logger.info(f"Total violations: {stats['total_violations']}")
    logger.info(f"Severity breakdown:")
    logger.info(f"  LOW: {stats['severity_counts']['low']}")
    logger.info(f"  MEDIUM: {stats['severity_counts']['medium']}")
    logger.info(f"  HIGH: {stats['severity_counts']['high']}")
    logger.info(f"\nKafka statistics:")
    logger.info(f"  Messages sent: {stats['kafka_sent']}")
    if stats['kafka_failed'] > 0:
        logger.warning(f"  Messages failed: {stats['kafka_failed']}")
    logger.info(f"\nResults saved to: {output_file}")
    logger.info("="*50)

if __name__ == "__main__":
    main()
