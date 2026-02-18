from typing import Optional, List, Any
from sqlmodel import Field, SQLModel, create_engine, Session  # type: ignore
from datetime import datetime
# vFinal Imports
from src.operative_core.models.memory import KnowledgeVector, EntityNode, EntityEdge, RegulationRule
from src.engines.economics import CostEvent
from src.engines.observability import AuditLog, ThoughtStream

# --- Database Models ---

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str = "Brand Identity"  # Brand Identity | Web Design | Packaging | Product Design
    client: Optional[str] = None
    status: str = "Intake"
    review_status: str = "PENDING" # PENDING, APPROVED, REJECTED, INCUBATING
    client_brief: str
    budget_cap: float
    budget_spent: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # NEW: Visual Cache for Studio OS (v7.0)
    executive_summary: Optional[str] = None
    strategy_json: Optional[str] = None # Compressed Brand DNA
    research_insights_json: Optional[str] = None # Competitive Gaps
    strategic_tensions: Optional[str] = None # NEW v15.0: "Luxury vs Accessible", etc.
    design_principles: Optional[str] = None # NEW v15.0: "Radical Simplicity", etc.
    timeline_json: Optional[str] = None # Phases & Deadlines
    deliverables_json: Optional[str] = None # Asset Status
    risks_json: Optional[str] = None # Flagged Items
    health_score: int = 100 # 0-100%
    active_agent: Optional[str] = None # Current agent working
    last_node: Optional[str] = None # Last successfully completed node
    raw_state_json: Optional[str] = None # Full StudioState snapshot
    cycle_count: int = 0 # Loop tracking
    internal_margin: float = 0.0 # From CFO
    internal_cost: float = 0.0 # From CFO
    is_locked: bool = False # Financial Lock Status
    
    # NEW: Founder Cockpit Indices (v12.0)
    stage: str = "Strategy" # Strategy, Design, Delivery, Closed
    next_milestone: Optional[str] = "Initial Synthesis"
    deadline: Optional[datetime] = None
    is_lead: bool = False # For Pipeline View
    blocker_summary: Optional[str] = None
    scope_stability: str = "Stable" # NEW v15.0: Stable, Drifting, Volatile
    margin_trend: str = "Flat" # NEW v15.0: Up, Flat, Down
    
    last_pulse: datetime = Field(default_factory=datetime.utcnow) # Last real-time update

    # NEW: Founder OS v14.0 Financials
    projected_revenue: float = 0.0
    invoiced_total: float = 0.0


class AgentLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    agent_name: str
    message: str
    severity: str = "INFO" # INFO, WARN, ERROR
    cost_incurred: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class InterventionRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    requesting_agent: str
    description: str
    cost_implication: float
    status: str = "PENDING" # PENDING, APPROVED, DENIED
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CalendarEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = "Virtual"
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    is_critical: bool = False

class GlobalTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    due_date: datetime
    priority: str = "Normal" # High, Normal, Low
    status: str = "Todo" # Todo, Done
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")

# --- Founder OS v14.0 New Tables ---

class Deliverable(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    title: str
    status: str = "Pending" # Pending, In Progress, Review, Approved
    due_date: Optional[datetime] = None
    owner: str = "Agent"

class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    name: str
    category: str = "General" # Folder: Strategy, Legal, Assets
    doc_type: str = "text" # text, link, file
    content: Optional[str] = None # Editable content
    url: Optional[str] = None # External link
    version: int = 1
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AgentRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    target_agent: str # "Director", "Strategist", "Designer", "CFO"
    request: str
    status: str = "Pending" # Pending, In Progress, Completed
    response: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Risk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    description: str
    severity: str = "Low" # Low, Medium, High, Critical
    category: str = "General" # Scope, Timeline, Budget, Client
    status: str = "Active" # Active, Mitigated, Accepted

class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    amount: float
    status: str = "Draft" # Draft, Sent, Overdue, Paid
    due_date: Optional[datetime] = None

class WorkflowStep(SQLModel, table=True):
    """Agent Workflow Engine — tracks cascading agent work and decision gates."""
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    step_type: str        # agent_output | decision_gate | approval_gate | input_needed | milestone
    agent: str            # Strategist | Director | Designer | CFO
    title: str
    body: str             # Full content (markdown)
    options_json: str = "[]"    # JSON array of options for decision/approval gates
    chosen_option: Optional[str] = None
    status: str = "active"      # pending | active | resolved | skipped
    phase: str = "strategy"     # strategy | design | production
    sort_order: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

# --- Database Setup ---
sqlite_file_name = "storage/studio.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)

# --- Real-Time Sync Utility (ProjectOS) ---

class ProjectOS:
    """
    Centralized utility for agents to sync their intelligence to the Studio OS.
    Ensures real-time updates for the cloud dashboard.
    """
    @staticmethod
    def update_intelligence(project_id: int, key: str, value: Any):
        """Pushes structured intelligence to a specific project field."""
        import json
        with Session(engine) as session:
            project = session.get(Project, project_id)
            if project:
                if key == "strategy":
                    project.strategy_json = json.dumps(value)
                elif key == "research":
                    project.research_insights_json = json.dumps(value)
                elif key == "timeline":
                    project.timeline_json = json.dumps(value)
                elif key == "dod":
                    project.deliverables_json = json.dumps(value)
                elif key == "risks":
                    project.risks_json = json.dumps(value)
                
                project.last_pulse = datetime.utcnow()
                session.add(project)
                session.commit()

    @staticmethod
    def update_status(project_id: int, agent_name: str, status: str, cycles: Optional[int] = None):
        """Updates the operational pulse, translates status, and recalculates health."""
        # Translate to Founder Language
        clean_status = AgentTranslator.translate(agent_name, status)
        
        with Session(engine) as session:
            project = session.get(Project, project_id)
            if project:
                project.active_agent = agent_name
                project.status = clean_status
                if cycles is not None:
                    project.cycle_count = cycles
                
                # DERIVE REAL HEALTH
                # Logic: 100 - (cycles * 15) - (total errors * 5)
                from sqlmodel import select, func # type: ignore
                error_count = session.exec(
                    select(func.count(AgentLog.id)).where(AgentLog.project_id == project_id, AgentLog.severity == "ERROR")
                ).one()
                
                health = 100 - (project.cycle_count * 15) - (error_count * 5)
                project.health_score = max(0, min(100, health))
                
                project.last_pulse = datetime.utcnow()
                session.add(project)
                session.commit()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

class AgentTranslator:
    """Translates technical agent logs into Founder-level insights."""
    
    DICTIONARY = {
        "Researcher": {
            "Market Audit Synthesized.": "Market Intelligence Report Generated.",
            "Analyzing brief...": "Scanning market gaps and competitor landscape...",
            "Market Research report generated locally.": "Intelligence gathering complete."
        },
        "CFO": {
            "Generating Quotation": "Financial Plan & Margin Analysis in progress.",
            "Financial Lock Activated": "Project Budget Alert: Review Required."
        },
        "Director": {
            "Synthesizing": "Executive Summary & Briefing Pack production active.",
            "Studio OS Dashboard synchronized.": "Operational state finalized for review.",
            "director Active": "Synthesizing Executive Architecture...",
            "Executive Briefing Ready": "Review Required: Strategic Briefing Pack generated."
        },
        "Strategist": {
            "Analyzing Brief": "Strategic Guardrail Alignment in progress.",
            "Live Strategic Intelligence Mirroring...": "Brand DNA & Positioning drafted."
        }
    }

    @staticmethod
    def translate(agent: str, message: str) -> str:
        agent_dict = AgentTranslator.DICTIONARY.get(agent, {})
        for raw, clean in agent_dict.items():
            if raw in message:
                return clean
        return message
