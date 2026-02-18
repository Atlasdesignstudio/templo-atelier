from typing import Dict, Any, List
from src.operative_core.agent_base import BaseAgent, AgentInput, AgentOutput
from src.dashboard_api.agent_intel import recommend_deliverables_llm

class DirectorAgent(BaseAgent):
    """
    Command Guild Leader.
    Responsible for budget, scope, and final approval.
    """
    def __init__(self):
        super().__init__(name="The Director", role="Command Guild Lead")

    def run(self, input_data: AgentInput) -> AgentOutput:
        task = input_data.task_description
        self._log(f"Received task: {task}")
        
        # Scenario: Recommend Deliverables
        if task == "recommend_deliverables":
            brief = input_data.context_data.get("brief", "")
            project_name = input_data.context_data.get("project_name", "Unknown Project")
            budget = int(input_data.parameters.get("budget", 5000))
            catalog = input_data.parameters.get("catalog", [])
            
            self._log(f"Analyzing brief for {project_name} with budget ${budget}...")
            
            # Use v18 LLM logic (Phase 2 Stub)
            # In Phase 3, this would be routed via ToolRouter -> Methodology Engine
            selected_keys = recommend_deliverables_llm(project_name, brief, budget, catalog)
            
            return AgentOutput(
                content=f"Recommended deliverables: {selected_keys}",
                structured_data={"selected_keys": selected_keys},
                confidence=0.9
            )
            
        return AgentOutput(content="Task not recognized.", confidence=0.0)

class OpsDirector(BaseAgent):
    """
    Command Guild Operations.
    Handling scheduling and logging.
    """
    def __init__(self):
        super().__init__(name="Ops Director", role="Operations")

    def run(self, input_data: AgentInput) -> AgentOutput:
        self._log("Ops processing...")
        return AgentOutput(content="Ops task logged.", confidence=1.0)
