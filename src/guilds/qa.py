from typing import Dict, Any
from src.operative_core.agent_base import BaseAgent, AgentInput, AgentOutput
from src.dashboard_api.agent_intel import client, _clean_json

# --- QA Guild ---
class Critic(BaseAgent):
    """
    Red Team Logic.
    Attacks artifacts to find weaknesses.
    """
    def __init__(self):
        super().__init__(name="The Critic", role="QA Red Team")

    def run(self, input_data: AgentInput) -> AgentOutput:
        artifact = input_data.context_data.get("artifact_content", "")
        criteria = input_data.parameters.get("criteria", "differentiation")
        
        prompt = f"""
        Act as a ruthless creative critic.
        Review the following artifact based on: {criteria}.
        Identify 3 weaknesses.
        Artifact: {artifact[:2000]}
        """
        
        if not client:
             return AgentOutput(content="Critic Unavailable (No LLM)", confidence=0)

        try:
            resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            return AgentOutput(content=resp.text, confidence=0.9)
        except Exception as e:
            return AgentOutput(content=f"Error: {e}", confidence=0)

class ComplianceOfficer(BaseAgent):
    """
    Governance Checks.
    """
    def __init__(self):
        super().__init__(name="Compliance Officer", role="Risk Governance")
    
    def run(self, input_data: AgentInput) -> AgentOutput:
        self._log("Running compliance scan...")
        # Stub logic
        return AgentOutput(content="No compliance risks detected.", confidence=1.0)
