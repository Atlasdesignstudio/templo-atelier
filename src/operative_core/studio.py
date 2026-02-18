from typing import Dict, Any, Optional

# Engines
from src.engines.orchestrator import OrchestrationEngine
from src.engines.economics import EconomicsEngine
from src.engines.perception import PerceptionEngine
from src.engines.learning import LearningEngine
from src.engines.tool_router import ToolRouter
from src.engines.observability import ObservabilityEngine
from src.engines.governance import GovernanceEngine

# Guilds
from src.guilds.command import DirectorAgent, OpsDirector
from src.guilds.strategy import BrandStrategist, Anthropologist, Semiotician
from src.guilds.qa import Critic, ComplianceOfficer
from src.guilds.production import DocumentProducer, SystemsLibrarian

class StudioInstance:
    """
    Singleton-like wrapper for the entire Templo Atelier System (vFinal).
    Central integration point.
    """
    _instance = None

    def __init__(self):
        # 1. Initialize Engines
        self.orchestrator = OrchestrationEngine()
        self.economics = EconomicsEngine()
        self.perception = PerceptionEngine()
        self.learning = LearningEngine()
        self.tool_router = ToolRouter()
        self.observability = ObservabilityEngine()
        self.governance = GovernanceEngine()

        # 2. Initialize Agents
        self.agents = {
            # Command
            "director": DirectorAgent(),
            "ops": OpsDirector(),
            # Strategy
            "strategist": BrandStrategist(),
            "anthropologist": Anthropologist(),
            "semiotician": Semiotician(),
            # QA
            "critic": Critic(),
            "compliance": ComplianceOfficer(),
            # Production
            "document_producer": DocumentProducer(),
            "librarian": SystemsLibrarian(),
        }

        # 3. Wire Dependencies (if any)
        # e.g., Agents need access to ToolRouter? 
        # For now, BaseAgent assumes stateless run, but we can inject context via Orchestrator state.

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

# --- Global Accessor ---
studio = StudioInstance() # Global singleton for main.py access
