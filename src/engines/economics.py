from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField
from datetime import datetime
import uuid

# --- Models ---
class Budget(BaseModel):
    project_id: str
    total_cap: float
    current_burn: float = 0.0
    currency: str = "USD"
    
    @property
    def remaining(self) -> float:
        return self.total_cap - self.current_burn

class CostEvent(SQLModel, table=True):
    id: str = SQLField(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    timestamp: datetime = SQLField(default_factory=datetime.utcnow)
    project_id: str
    agent_name: str
    tool_name: str
    tokens_used: int = 0
    cost_amount: float = 0.0
    description: str

class Quote(BaseModel):
    project_id: str
    estimated_cost: float
    rationale: str
    valid_until: datetime

# --- Engine ---
class EconomicsEngine:
    def __init__(self):
        self.budgets: Dict[str, Budget] = {}
        self.ledger: List[CostEvent] = []
        # Pricing (Illustrative)
        self.rates = {
            "token_input": 0.000001,  # $1 per 1M
            "token_output": 0.000002,
            "tool_call": 0.01 
        }

    def set_budget(self, project_id: str, cap: float):
        self.budgets[project_id] = Budget(project_id=project_id, total_cap=cap)

    def log_cost(self, project_id: str, agent: str, tool: str, tokens_in: int = 0, tokens_out: int = 0):
        cost = (tokens_in * self.rates["token_input"]) + \
               (tokens_out * self.rates["token_output"]) + \
               self.rates["tool_call"]
        
        event = CostEvent(
            project_id=project_id,
            agent_name=agent,
            tool_name=tool,
            tokens_used=tokens_in + tokens_out,
            cost_amount=cost,
            description=f"Action by {agent} using {tool}"
        )
        self.ledger.append(event)
        # TODO: Persist via Session (requires Studio injection of session)
        
        if project_id in self.budgets:
            self.budgets[project_id].current_burn += cost

    def check_budget(self, project_id: str) -> bool:
        """Returns True if budget is available."""
        if project_id not in self.budgets:
            return True # uncapped if not set
        return self.budgets[project_id].remaining > 0

    def generate_quote(self, project_id: str, complexity_score: int) -> Quote:
        """Stub logic for quote generation."""
        base_rate = 500.0
        estimate = base_rate * complexity_score
        return Quote(
            project_id=project_id,
            estimated_cost=estimate,
            rationale=f"Base ${base_rate} x Complexity {complexity_score}",
            valid_until=datetime.utcnow()
        )
