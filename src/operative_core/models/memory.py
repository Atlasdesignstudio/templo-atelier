from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

# --- Vector Memory ---
class KnowledgeVector(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    content: str
    embedding: str  # JSON string of vector
    vector_type: str = Field(default="document")  # document, snippet, rule
    meta_json: str = Field(default="{}")  # Extra metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- Graph Memory --
class EntityNode(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    category: str  # e.g., "Client", "Industry", "Competitor"
    attributes: str = Field(default="{}")  # JSON storage for flexible attributes
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EntityEdge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: str = Field(foreign_key="entitynode.id")
    target_id: str = Field(foreign_key="entitynode.id")
    relation: str = Field(index=True)  # e.g., "prefers", "conflicts_with"
    weight: float = Field(default=1.0)
    context: Optional[str] = None

# --- Rules Store ---
class RegulationRule(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    domain: str = Field(index=True)  # e.g., "Healthcare", "Finance"
    rule_content: str
    strictness: int = Field(default=5)  # 1-10
    source: Optional[str] = None
    active: bool = Field(default=True)
