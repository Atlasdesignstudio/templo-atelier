from typing import List, Dict
import json
from src.operative_core.agent_base import BaseAgent, AgentInput, AgentOutput
from src.dashboard_api.agent_intel import client, _clean_json
from src.dashboard_api.agent_intel import generate_strategic_directions_llm, expand_strategy_llm, generate_roadmap_llm

class BrandStrategist(BaseAgent):
    """
    Lead Creative Direction.
    Generates strategic directions and brand pillars.
    """
    def __init__(self):
        super().__init__(name="The Strategist", role="Strategy Lead")

    def run(self, input_data: AgentInput) -> AgentOutput:
        self._log(f"Received strategy task: {input_data.task_description}")
        project_name = input_data.context_data.get("project_name", "Unknown")
        brief = input_data.context_data.get("brief", "")
        
        if input_data.task_description == "generate_directions":
            # Use v18 function for now
            directions = generate_strategic_directions_llm(project_name, brief)
            return AgentOutput(
                content=json.dumps(directions, indent=2),
                structured_data={"directions": directions},
                confidence=0.85
            )

        if input_data.task_description == "create_roadmap":
            research_context = input_data.context_data.get("research_context", "")
            category = input_data.context_data.get("category", "Brand Identity")
            roadmap = generate_roadmap_llm(project_name, brief, research_context, category)
            return AgentOutput(
                content=json.dumps(roadmap, indent=2),
                structured_data={"roadmap": roadmap},
                confidence=0.9
            )

        if input_data.task_description == "expand_strategy":
            direction = input_data.context_data.get("direction", {})
            strategy = expand_strategy_llm(project_name, brief, direction)
            return AgentOutput(
                content=json.dumps(strategy, indent=2),
                structured_data={"strategy": strategy},
                confidence=0.9
            )
        
        return AgentOutput(content="Task not supported.", confidence=0)

class Anthropologist(BaseAgent):
    """
    Cultural & Market Sensing.
    """
    def __init__(self):
        super().__init__(name="The Anthropologist", role="Cultural Analyst")

    def run(self, input_data: AgentInput) -> AgentOutput:
        brief = input_data.context_data.get("brief", "")
        project_name = input_data.context_data.get("project_name", "")
        
        # FIXED: Escaped braces for JSON structure inside f-string
        prompt = f"""
        Act as a Cultural Anthropologist.
        Analyze the cultural context for: {project_name} - {brief}.
        Identify 3 major cultural shifts relevant to this brand.
        Return JSON list of {{'shift': str, 'implication': str}}.
        """
        
        if not client:
            return AgentOutput(content="LLM Unavailable", confidence=0)
            
        try:
            resp = client.models.generate_content(
                model="gemini-2.0-flash", contents=prompt
            )
            data = json.loads(_clean_json(resp.text))
            return AgentOutput(
                content=resp.text,
                structured_data={"shifts": data},
                confidence=0.8
            )
        except Exception as e:
            self._log(f"Error: {e}")
            return AgentOutput(content=f"Error: {e}", confidence=0)

class Semiotician(BaseAgent):
    """
    Visual Code Analysis.
    """
    def __init__(self):
        super().__init__(name="The Semiotician", role="Visual Analyst")

    def run(self, input_data: AgentInput) -> AgentOutput:
        brief = input_data.context_data.get("brief", "")
        # Mock logic or LLM call similar to Anthropologist
        # For Phase 2 minimal viable product:
        return AgentOutput(
            content="Semiotic analysis placeholder.",
            structured_data={"codes": ["minimalism", "bold_typography"]},
            confidence=0.5
        )
