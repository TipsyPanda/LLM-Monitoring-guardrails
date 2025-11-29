from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict
from enum import Enum
import numpy as np

def convert_numpy_types(obj):
    """
    Recursively convert numpy types to native Python types for JSON serialization.

    Handles:
    - numpy scalars (float32, int64, bool_, etc.) -> Python primitives
    - numpy arrays -> Python lists
    - Nested dictionaries and lists

    Args:
        obj: Any object that may contain numpy types

    Returns:
        Object with all numpy types converted to native Python types
    """
    if isinstance(obj, np.generic):
        # Convert numpy scalar to native Python type using .item()
        return obj.item()
    elif isinstance(obj, np.ndarray):
        # Convert numpy array to list
        return obj.tolist()
    elif isinstance(obj, dict):
        # Recursively convert dictionary values
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        # Recursively convert list/tuple items, preserving type
        return type(obj)(convert_numpy_types(item) for item in obj)
    return obj

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
        data['metadata'] = convert_numpy_types(data['metadata'])
        return data
