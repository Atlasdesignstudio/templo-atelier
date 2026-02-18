from typing import Dict, Any, Optional
import os
import json
from google import genai  # type: ignore
from src.shared.logger import AgentLogger  # type: ignore
from src.shared.drive_utils import (  # type: ignore
    get_drive_service,
    get_docs_service,
    find_folder,
    ensure_folder,
    create_google_doc
)

def director_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    The Director Agent (Briefing Synthesizer)
    Role: Consolidates all agent intelligence into the 'Creative Briefing Pack'.
    Hides creative noise, surfaces strategic guardrails.
    """
    project_id = state.get("project_id", 1)
    project_name = state.get("project_name", "Unknown Project")
    logger = AgentLogger(project_id)
    
    print(f"--- [Agent] The Director: Synthesizing {project_name} for Executive Review ---")
    logger.log("Director", "Generating Executive Surface Layer...")

    # Check for Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"executive_summary": "Director mode disabled (No API Key)."}

    client = genai.Client(api_key=api_key)
    
    # Context Aggregation
    research = state.get("market_research", "Standard research applied.")
    strategy = state.get("brand_dna_json", {})
    finance = state.get("project_status", "Active")
    critic = state.get("critic_feedback", "Passed internal audit.")
    cycle_count = state.get("cycle_count", 1)
    questions = state.get("clarifying_questions", [])
    
    # The Prompt for Briefing Synthesis
    prompt = f"""
    You are the Managing Director of Templo Atelier.
    Your task is to synthesize the strategic intelligence from several agents into a 
    'Creative Briefing Pack' for the Human Creative Lead.
    
    [RAW INTELLIGENCE]
    - Project: {project_name}
    - Research: {state.get("market_research", "")[:600]}
    - Strategy Guardrails: {state.get("brand_dna_json", {})}
    - UX/Design Intel: {state.get("ux_arch_path", "Pending")} | {state.get("design_intel_path", "Pending")}
    - Operational Context: {state.get("project_status", "Active")}
    
    [OBJECTIVE]
    Do NOT generate creative work. Generate STRATEGIC GUARDRAILS.
    Focus on "Definition of Done", "Tradeoffs", and "Evaluation Criteria".
    
    [OUTPUT FORMAT]
    Return a JSON object:
    {{
      "briefing_pack_markdown": "# 00_CREATIVE_BRIEFING_PACK: {project_name} ... (Full Markdown)",
      "dashboard_metrics": {{
        "executive_summary": "Vision for the Human Lead.",
        "guardrails": ["Principle 1", "Boundary 1"],
        "strategic_tradeoffs": ["Context A > Context B"],
        "risks": [{{ "item": "Risk", "severity": "HIGH" }}],
        "definition_of_done": ["Requirement 1"],
        "health_score": 0-100
      }}
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={ "response_mime_type": "application/json" }
        )
        data = json.loads(response.text.strip())
        briefing_content = data["briefing_pack_markdown"]
        metrics = data["dashboard_metrics"]
        
        # 1. Update Drive (The Briefing Pack)
        try:
            drive = get_drive_service()
            docs = get_docs_service()
            root_id = find_folder(drive, "Templo Atelier")
            projects_id = find_folder(drive, "05_Projects", root_id)
            project_folder_id = find_folder(drive, project_name, projects_id)
            
            if project_folder_id:
                create_google_doc(drive, docs, f"00_CREATIVE_BRIEFING_PACK - {project_name}", project_folder_id, briefing_content)
                logger.log("Director", "Creative Briefing Pack pushed to Drive.")
        except Exception as e:
            logger.log("Director", f"Drive push failed: {e}", severity="WARN")

        # 2. Update DB (Dashboard OS)
        from src.shared.db import Project, Session, engine # type: ignore
        with Session(engine) as session:
            project = session.get(Project, project_id)
            if project:
                project.executive_summary = metrics["executive_summary"]
                project.strategy_json = json.dumps(metrics["guardrails"])
                project.research_insights_json = json.dumps(metrics["strategic_tradeoffs"])
                project.risks_json = json.dumps(metrics["risks"])
                project.deliverables_json = json.dumps(metrics["definition_of_done"])
                project.health_score = metrics["health_score"]
                
                # NEW: Founder Cockpit Integration (v12.0)
                project.review_status = "PENDING"
                project.stage = "Strategy" # Director is at end of Strategy
                project.status = "Executive Briefing Ready"
                project.next_milestone = "Human Sign-off"
                project.blocker_summary = "Awaiting Founder Approval"
                
                session.add(project)
                session.commit()
            logger.log("Director", "Studio OS Dashboard synchronized.")

        return {"briefing_pack": briefing_content}

    except Exception as e:
        logger.log("Director", f"Synthesis failed: {e}", severity="ERROR")
        return {"executive_summary": "Failed to generate summary."}
