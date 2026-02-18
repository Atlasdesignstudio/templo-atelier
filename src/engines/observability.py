from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField
from datetime import datetime
import json
import uuid

# --- Models ---
class AuditLog(SQLModel, table=True):
    id: str = SQLField(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    timestamp: datetime = SQLField(default_factory=datetime.utcnow)
    project_id: str
    agent_name: str
    action: str  # e.g., "Decision Gate", "Tool Call", "System Error"
    details_json: str = "{}" # SQLModel doesn't support Dict directly, storing as JSON string
    severity: str = "INFO"
    
    @property
    def details(self) -> Dict:
        return json.loads(self.details_json)

class ThoughtStream(SQLModel, table=True):
    id: str = SQLField(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    timestamp: datetime = SQLField(default_factory=datetime.utcnow)
    project_id: str
    agent_name: str
    content: str  # The "inner monologue" or reasoning

# --- Engine ---
class ObservabilityEngine:
    def __init__(self):
        self.audit_trail: List[AuditLog] = []
        self.stream_log: List[ThoughtStream] = []

    def log_event(self, project_id: str, agent: str, action: str, details: Dict = {}, severity: str = "INFO"):
        event = AuditLog(
            project_id=project_id,
            agent_name=agent,
            action=action,
            details_json=json.dumps(details),
            severity=severity
        )
        self.audit_trail.append(event)
        # TODO: Persist to File/DB (Phase 5)

    def log_thought(self, project_id: str, agent: str, content: str):
        thought = ThoughtStream(
            project_id=project_id,
            agent_name=agent,
            content=content
        )
        self.stream_log.append(thought)

    def fetch_stream(self, project_id: str, limit: int = 10) -> List[ThoughtStream]:
        proj_stream = [t for t in self.stream_log if t.project_id == project_id]
        return sorted(proj_stream, key=lambda x: x.timestamp)[-limit:]
