import json
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from loguru import logger
from typing import Iterator
from src.models.conversation import Conversation


class ConversationConsumer:
    """Kafka consumer for receiving LLM conversation events"""

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str = "llm.conversations",
        consumer_group: str = "guardrail-input-processor-group",
        enabled: bool = True
    ):
        """
        Initialize the Kafka consumer

        Args:
            bootstrap_servers: Kafka bootstrap servers (e.g., "localhost:9092")
            topic: Topic name to consume conversations from
            consumer_group: Consumer group ID for Kafka
            enabled: Whether Kafka consumer is enabled
        """
        self.enabled = enabled
        self.topic = topic
        self.consumer_group = consumer_group
        self.receive_count = 0
        self.error_count = 0

        if not self.enabled:
            logger.info("Kafka conversation consumer is disabled")
            return

        try:
            self.consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers.split(','),
                group_id=consumer_group,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            logger.info(f"Kafka conversation consumer initialized: {bootstrap_servers}, topic: {topic}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            self.enabled = False
            raise

    def consume_conversations(self) -> Iterator[Conversation]:
        """
        Generator that yields Conversation objects from Kafka

        Yields:
            Conversation objects as they arrive
        """
        if not self.enabled:
            return

        for message in self.consumer:
            try:
                conversation = Conversation.from_dict(message.value)
                self.receive_count += 1
                logger.debug(f"Received conversation: {conversation.conversation_id}")
                yield conversation
            except Exception as e:
                logger.warning(f"Error parsing conversation message: {e}")
                self.error_count += 1
                continue

    def close(self):
        """Close the consumer"""
        if self.enabled and hasattr(self, 'consumer'):
            try:
                logger.info(f"Closing Kafka consumer (received: {self.receive_count}, errors: {self.error_count})")
                self.consumer.close()
                logger.info("Kafka consumer closed successfully")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer: {e}")

    def get_stats(self):
        """Get consumer statistics"""
        return {
            'enabled': self.enabled,
            'received': self.receive_count,
            'errors': self.error_count
        }
