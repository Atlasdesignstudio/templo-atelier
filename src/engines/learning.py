from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# --- Models ---
class PreferenceNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str
    key: str
    value: str
    confidence: float = 1.0

class FeedbackEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    artifact_id: str
    feedback_text: str
    sentiment: str = "neutral"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# --- Engine ---
class LearningEngine:
    def __init__(self):
        self.preferences: List[PreferenceNode] = []
        self.feedback_log: List[FeedbackEvent] = []

    def ingest_feedback(self, artifact_id: str, feedback_text: str):
        event = FeedbackEvent(artifact_id=artifact_id, feedback_text=feedback_text)
        self.feedback_log.append(event)
        # TODO: Parse feedback to update preferences (Phase 5 AI loop)
        # For now, simplistic rule: store it.

    def get_preferences(self, domain: str) -> List[PreferenceNode]:
        return [p for p in self.preferences if p.domain == domain]

    def optimize_prompt(self, original_prompt: str, domain: str) -> str:
        """
        Injects preferences into the prompt (DSPy-style scaffold injection).
        """
        prefs = self.get_preferences(domain)
        if not prefs:
            return original_prompt
        
        injection = "\n".join([f"- PREFER: {p.value}" for p in prefs])
        return f"{original_prompt}\n\n[Learned Preferences]:\n{injection}"
