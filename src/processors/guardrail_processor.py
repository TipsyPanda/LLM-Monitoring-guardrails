import guardrails as gd
from guardrails.hub import ToxicLanguage
from detoxify import Detoxify
from typing import Optional
from src.models.conversation import Conversation
from src.models.violation import Violation, SeverityLevel
from loguru import logger

class GuardrailProcessor:
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

        # Initialize guardrails with ToxicLanguage
        self.guard = gd.Guard().use(
            ToxicLanguage(
                threshold=threshold,
                validation_method="sentence",
                on_fail="exception"
            )
        )

        # Direct detoxify model for detailed scores
        self.detoxify_model = Detoxify('original')
        logger.info(f"GuardrailProcessor initialized with threshold={threshold}")

    def process_conversation(self, conversation: Conversation) -> Optional[Violation]:
        """Process conversation and return violation if detected"""
        try:
            # Validate with guardrails
            self.guard.validate(conversation.text)
            return None  # No violation

        except Exception as e:
            # Violation detected - get detailed analysis
            scores = self.detoxify_model.predict(conversation.text)

            # Extract which labels are toxic
            toxic_labels = [
                label for label, score in scores.items()
                if score > self.threshold
            ]

            # Calculate severity
            severity = self._calculate_severity(scores)

            return Violation(
                conversation_id=conversation.conversation_id,
                timestamp=conversation.timestamp,
                original_text=conversation.text,
                toxic_sentences=[conversation.text],  # Simplified for prototype
                toxicity_labels=toxic_labels,
                severity=severity,
                metadata={'scores': scores}
            )

    def _calculate_severity(self, scores: dict) -> SeverityLevel:
        """
        Classify severity based on toxicity scores:
        - HIGH: severe_toxicity/threat/identity_attack > 0.7
        - MEDIUM: any score > 0.6 OR multiple violations
        - LOW: any score > threshold
        """
        high_priority = ['severe_toxicity', 'threat', 'identity_attack']

        # Check for high severity
        for label in high_priority:
            if scores.get(label, 0) > 0.7:
                return SeverityLevel.HIGH

        # Check for medium severity
        violations_count = sum(1 for score in scores.values() if score > self.threshold)
        if violations_count >= 2 or max(scores.values()) > 0.6:
            return SeverityLevel.MEDIUM

        return SeverityLevel.LOW
