import os
import json
from typing import Dict, Any, List
from google import genai  # type: ignore
from pathlib import Path

# Shared Utilities
from src.shared.drive_utils import (  # type: ignore
    get_drive_service,
    find_folder,
    ensure_folder,
    upload_file
)
from src.shared.logger import AgentLogger  # type: ignore

def researcher_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chief Research Officer
    Role: Performs autonomous market and competitor research using Gemini 2.0 Flash.
    """
    print("--- [Agent] Chief Research Officer: Performing Market Audit ---")
    
    project_id = state.get("project_id", 1)
    logger = AgentLogger(project_id)
    
    # Check for Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
         print("!! NO API KEY FOUND !! Returning Mock Research")
         return {"market_research": "Mock research data: Competition is high in the solar skincare niche."}
    
    # Init GenAI Client
    client = genai.Client(api_key=api_key)
    
    project_name = state.get("project_name", "Unknown Project")
    brief = state.get("client_brief", "")
    
    # Phase 1: Search Query Generation & Simulation
    # In a full v3.0, this would call Tavily/Google Search.
    # For this phase, we let Gemini "simulate" a deep research audit based on its internal knowledge 
    # of the niche described in the brief.
    
    prompt = f"""
    You are the Chief Research Officer of Templo Atelier. 
    Your goal is to provide a "million assistants" level of research for the following project.
    
    Project: {project_name}
    Brief: {brief}
    
    Perform a deep-dive research audit including:
    1. Market Overview: Trends and current state of the industry.
    2. Competitive Audit: Top 3 types of competitors and what they do well.
    3. Target Audience Insights: Psychographics and pain points.
    4. Best Practices: Strategic "do's and don'ts" for this specific category.
    
    Format your output as a professional Markdown report.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        research_report = response.text.strip()
        
        # --- [Persistence & Mirroring] ---
        project_id = state.get("project_id", 1)
        # Create local folder if not exists
        research_dir = Path(f"projects/2026/{project_name.replace(' ', '_')}/01_Strategy")
        research_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = research_dir / "Market_Research.md"
        with open(report_path, "w") as f:
            f.write(research_report)
            
        logger.log("Researcher", "Market Research report generated locally.")

        # --- Real-Time OS Sync ---
        from src.shared.db import ProjectOS # type: ignore
        ProjectOS.update_intelligence(project_id, "research", {"report_snippet": research_report[:500] + "..."})
        ProjectOS.update_status(project_id, "Researcher", "Market Audit Synthesized.")

        # Drive Mirroring
        try:
            drive = get_drive_service()
            root_id = find_folder(drive, "Templo Atelier")
            projects_id = find_folder(drive, "05_Projects", root_id)
            project_folder_id = find_folder(drive, project_name, projects_id)
            
            if project_folder_id:
                strategy_folder_id = ensure_folder(drive, "01_Strategy", project_folder_id)
                if strategy_folder_id:
                    upload_file(drive, str(report_path), strategy_folder_id)
                    logger.log("Researcher", "Market Research mirrored to Google Drive.")
        except Exception as drive_err:
            logger.log("Researcher", f"Drive mirroring failed: {drive_err}", severity="WARN")

    except Exception as e:
        print(f"Error in Research Agent: {e}")
        research_report = f"Research failed: {e}"
        
    return {"market_research": research_report}

if __name__ == "__main__":
    # Test
    sample_state = {
        "project_name": "Solaris Glow",
        "client_brief": "Luxury skincare for extreme altitude digital nomads."
    }
    print(researcher_agent(sample_state))
