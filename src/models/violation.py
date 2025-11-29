from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict
from enum import Enum

class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class Violation:
    conversation_id: str
    timestamp: datetime
    original_text: str
    toxic_sentences: List[str]
    toxicity_labels: List[str]
    severity: SeverityLevel
    metadata: Dict

    def to_dict(self):
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['severity'] = self.severity.value
        return data
