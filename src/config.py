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
