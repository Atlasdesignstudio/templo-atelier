from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
import time

# --- Task Contracts ---
class AgentInput(BaseModel):
    task_description: str
    context_data: Dict[str, Any] = {}  # Previous artifacts, constraints
    parameters: Dict[str, Any] = {}

class AgentOutput(BaseModel):
    content: str  # The main artifact
    structured_data: Dict[str, Any] = {}  # JSON data
    assumptions: List[str] = []
    evidence_links: List[str] = []
    confidence: float = 1.0
    execution_log: List[str] = []

class QAStatus(BaseModel):
    passed: bool
    issues: List[str] = []
    score: int = 0

# --- Base Agent ---
class BaseAgent(ABC):
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.log = []

    def _log(self, message: str):
        timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
        entry = f"{timestamp} [{self.name}] {message}"
        self.log.append(entry)
        print(entry)

    @abstractmethod
    def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Core logic for the agent. Must return structured output.
        """
        pass

    def qa_check(self, output: AgentOutput) -> QAStatus:
        """
        Self-verification stub. 
        Overwrite in subclasses or use GovernanceEngine.
        """
        self._log("Running self-check...")
        # Basic check: content not empty
        passed = bool(output.content and len(output.content) > 10)
        return QAStatus(
            passed=passed,
            issues=[] if passed else ["Content too short."]
        )
