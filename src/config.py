from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    DATASET_PATH: str = os.getenv("DATASET_PATH", "data/raw/conversations.csv")
    TOXICITY_THRESHOLD: float = float(os.getenv("TOXICITY_THRESHOLD", "0.5"))
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")
    HIGH_SEVERITY_THRESHOLD: float = 0.7
    MEDIUM_SEVERITY_THRESHOLD: float = 0.6

    # Kafka configuration
    KAFKA_ENABLED: bool = os.getenv("KAFKA_ENABLED", "false").lower() == "true"
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "guardrail.violations")

@dataclass
class AlertConfig:
    """Configuration for alert consumer service"""
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "guardrail.violations")
    ALERT_WINDOW_SIZE_SECONDS: int = int(os.getenv("ALERT_WINDOW_SIZE_SECONDS", "300"))
    ALERT_OUTPUT_FILE: str = os.getenv("ALERT_OUTPUT_FILE", "outputs/alerts.jsonl")
    ALERT_CONSUMER_GROUP: str = os.getenv("ALERT_CONSUMER_GROUP", "alert-consumer-group")
