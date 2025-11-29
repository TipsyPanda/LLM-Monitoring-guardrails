from dataclasses import dataclass
from datetime import datetime

@dataclass
class Conversation:
    conversation_id: str
    text: str
    timestamp: datetime
    speaker: str  # 'user' or 'agent'

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            conversation_id=data['conversation_id'],
            text=data['text'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            speaker=data.get('speaker', 'user')
        )
