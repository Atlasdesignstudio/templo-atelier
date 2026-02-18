from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# --- Models ---
class Signal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str
    signal_type: str  # trend_shift, competitor_move, etc.
    entity: str
    element: str  # specific topic
    observation: str
    evidence: List[Dict[str, str]] = []  # links
    confidence: float = 0.0
    tags: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# --- Engine ---
class PerceptionEngine:
    def __init__(self):
        self.reservoir: List[Signal] = []

    def ingest_signal(self, signal: Signal):
        self.reservoir.append(signal)
        # TODO: Persist to Vector Memory via MemorySystem?
        # For Phase 3 foundation: In-memory list (ephemeral) or append to file.

    def query_reservoir(self, topic: str) -> List[Signal]:
        """Simple keyword matching for now."""
        results = []
        topic = topic.lower()
        for sig in self.reservoir:
            if topic in sig.observation.lower() or topic in sig.entity.lower():
                results.append(sig)
        return results

    def generate_digest(self, domain: str) -> str:
        domain_signals = [s for s in self.reservoir if s.domain == domain]
        return f"Found {len(domain_signals)} signals for {domain}."
