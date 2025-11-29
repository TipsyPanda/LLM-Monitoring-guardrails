from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict
from loguru import logger


class SlidingWindowTracker:
    """
    Track violations per conversation in sliding time windows

    Maintains a 5-minute sliding window of violations per conversation_id.
    Automatically cleans expired violations to prevent memory leaks.
    """

    def __init__(self, window_size_seconds: int = 300):
        """
        Initialize the sliding window tracker

        Args:
            window_size_seconds: Size of the sliding window in seconds (default: 300 = 5 minutes)
        """
        self.window_size = window_size_seconds
        # Structure: {conversation_id: [(timestamp, violation), ...]}
        self.windows: Dict[str, List[Tuple[datetime, dict]]] = defaultdict(list)
        logger.info(f"SlidingWindowTracker initialized with {window_size_seconds}s window")

    def add_violation(self, violation: dict) -> int:
        """
        Add violation to the sliding window and return current count

        Args:
            violation: Violation dictionary with timestamp and conversation_id

        Returns:
            Current count of violations in the window for this conversation
        """
        conv_id = violation['conversation_id']
        timestamp = datetime.fromisoformat(violation['timestamp'])

        # Add new violation to window
        self.windows[conv_id].append((timestamp, violation))

        # Clean expired violations (older than window size)
        self._clean_expired(conv_id, timestamp)

        # Return current count in window
        count = len(self.windows[conv_id])
        logger.debug(f"Conversation {conv_id}: {count} violations in window")

        return count

    def _clean_expired(self, conv_id: str, current_time: datetime):
        """
        Remove violations outside the sliding window

        Args:
            conv_id: Conversation ID to clean
            current_time: Current timestamp for calculating cutoff
        """
        cutoff_time = current_time - timedelta(seconds=self.window_size)

        # Keep only violations within the window
        self.windows[conv_id] = [
            (ts, v) for ts, v in self.windows[conv_id]
            if ts >= cutoff_time
        ]

        # Remove empty windows to prevent memory leak
        if not self.windows[conv_id]:
            del self.windows[conv_id]
            logger.debug(f"Removed empty window for conversation {conv_id}")

    def get_violations(self, conv_id: str) -> List[dict]:
        """
        Get all violations in the current window for a conversation

        Args:
            conv_id: Conversation ID

        Returns:
            List of violation dictionaries in the current window
        """
        return [v for _, v in self.windows.get(conv_id, [])]

    def get_window_count(self, conv_id: str) -> int:
        """
        Get the count of violations in the window for a conversation

        Args:
            conv_id: Conversation ID

        Returns:
            Count of violations in the window
        """
        return len(self.windows.get(conv_id, []))
