from typing import Dict, Any
import os
import json
from google import genai  # type: ignore
from src.models import BrandDNA  # type: ignore

# Shared Utilities
from src.shared.drive_utils import (  # type: ignore
    get_drive_service,
    get_docs_service,
    find_folder,
    ensure_folder,
    create_google_doc,
    upload_file
)
from src.shared.logger import AgentLogger  # type: ignore
from src.shared.db import ProjectOS # type: ignore
from pathlib import Path

def strategy_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chief Strategy Agent
    Role: Analyzes the client brief, detects white-space opportunities, and maps 
    the brand DNA into strategic guardrails.
    """
    project_id = state.get("project_id", 1)
    logger = AgentLogger(project_id)
    print("--- [Agent] Chief Strategy Agent: Analyzing Brief ---")
    
    # Check for Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
         print("!! NO API KEY FOUND !! Returning Mock Strategic Intelligence")
         project_name = state.get("project_name", "Untitled")
         safe_name = project_name.replace(" ", "_").replace("/", "-")
         proj_root = Path("projects") / "2026" / safe_name
         strategy_dir = proj_root / "01_Strategy"
         strategy_dir.mkdir(parents=True, exist_ok=True)
         
         mock_intel = {
             "project_truth": "Mock: Wellness luxury furniture.",
             "white_space_map": "Mock: High-end sustainable lounge market.",
             "strategic_guardrails": ["Mock: Focus on organic curves", "Mock: Avoid industrial textures"],
             "design_principles": ["Elegance", "Wellness", "Nature"],
             "tone_of_voice_boundaries": ["Calm", "Sophisticated"],
             "what_not_to_do": ["No loud colors", "No synthetic materials"],
             "decision_criteria": ["Does it evoke serenity?"],
             "exploration_prompts": ["Sketch 3 modular lounge options"]
         }
         
         with open(strategy_dir / "strategic_intelligence.json", "w") as f:
             json.dump(mock_intel, f, indent=4)
         with open(strategy_dir / "Strategy_Deck.md", "w") as f:
             f.write("# Mock Strategy Deck\n\nGuardrails active.")
             
         # --- Real-Time OS Sync ---
         ProjectOS.update_intelligence(project_id, "strategy", mock_intel) # type: ignore
         ProjectOS.update_status(project_id, "Strategist", "Strategic Intelligence Established") # type: ignore
             
         return {"brand_dna_json": mock_intel}
    
    # Init GenAI Client
    client = genai.Client(api_key=api_key)
    
    feedback = state.get("critic_feedback", "CRITIC_PASSED")
    feedback_instruction = ""
    if feedback != "CRITIC_PASSED":
        feedback_instruction = f"""
        *** CRITICAL: PREVIOUS STRATEGY WAS REJECTED BY THE DESIGN CRITIC ***
        FEEDBACK TO FIX:
        {feedback}
        
        Please adjust the strategy to address these specific concerns.
        """
        
    prompt = f"""
    You are the Chief Strategy Officer of a world-class creative studio.
    Analyze the following client brief and market research.
    Your goal is NOT to create the brand, but to define the STRATEGIC GUARDRAILS that the human creative lead will use to design the brand.
    
    {feedback_instruction}
    
    Client Brief: {state["client_brief"]}
    Market Research: {state.get("market_research", "No specific research provided.")}
    
    YOUR TASK:
    1. Extract the "Project Truth": Structured constraints and distilled objective.
    2. Identify White-Space Opportunities: Where is the competitor gap?
    3. Define Positioning Options: Options A vs B with clear tradeoffs.
    4. Set Creative Guardrails: Principles, "What not to do", and tone of voice boundaries.
    5. Define Decision Criteria: 3 rules for evaluating the human's creative work.
    
    Return a JSON object only (no markdown formatting) with:
    - project_truth: str
    - white_space_map: str
    - positioning_options: list[dict(name, rationale, tradeoff)]
    - strategic_guardrails: list[str]
    - design_principles: list[str]
    - tone_of_voice_boundaries: list[str]
    - what_not_to_do: list[str]
    - decision_criteria: list[str]
    - exploration_prompts: list[str] (Prompts for the human to use during design)
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        
        # Clean JSON string
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3].strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:-3].strip()
            
        strategy_intel = json.loads(raw_text) # type: ignore
        
        # --- [Synthesis: Strategic Intelligence Doc] ---
        project_id = state.get("project_id", 1)
        logger = AgentLogger(project_id)
        
        # 1. Local Persistence
        # We assume projects are in projects/2026/{name}/
        project_name = state.get("project_name", "Untitled") # type: ignore
        safe_name = project_name.replace(" ", "_").replace("/", "-") # type: ignore
        proj_root = Path("projects") / "2026" / safe_name
        strategy_dir = proj_root / "01_Strategy"
        strategy_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON
        with open(strategy_dir / "strategic_intelligence.json", "w") as f:
            json.dump(strategy_intel, f, indent=4)
            
        # Generate Strategic Intelligence Deck
        deck_content = f"""# Templo Atelier: Strategic Intelligence — {project_name}
> Prepared for the Creative Lead (Human)

## 1. The Project Truth
{strategy_intel.get('project_truth', 'N/A')}

## 2. White-Space Map (Competitive Gaps)
{strategy_intel.get('white_space_map', 'N/A')}

## 3. Strategic Guardrails
### ✅ Principles
- {"\n- ".join(strategy_intel.get('strategic_guardrails', []))}

### ❌ What Not To Do
- {"\n- ".join(strategy_intel.get('what_not_to_do', []))}

## 4. Design & Tone Guardrails
- **Design Principles**: {", ".join(strategy_intel.get('design_principles', []))}
- **Tone Boundaries**: {", ".join(strategy_intel.get('tone_of_voice_boundaries', []))}

## 5. Evaluation Framework
### ⚖️ Decision Criteria
How to judge the final creative:
- {"\n- ".join(strategy_intel.get('decision_criteria', []))}

## 6. Design Exploration Prompts (For You)
- {"\n- ".join(strategy_intel.get('exploration_prompts', []))}

---
*Generated by Templo Atelier Strategic Intelligence Agent v9.0*
"""
        with open(strategy_dir / "Strategy_Deck.md", "w") as f:
            f.write(deck_content)
            
        logger.log("Strategist", "Strategy Deck & JSON generated locally.")

        # --- Real-Time OS Sync ---
        ProjectOS.update_intelligence(project_id, "strategy", strategy_intel)
        ProjectOS.update_status(project_id, "Strategist", "Live Strategic Intelligence Mirroring...")

        # 2. Drive Mirroring
        try:
            drive = get_drive_service()
            docs = get_docs_service()
            
            # Find Project Folder
            root_id = find_folder(drive, "Templo Atelier")
            projects_id = find_folder(drive, "05_Projects", root_id)
            project_folder_id = find_folder(drive, project_name, projects_id)
            if project_folder_id:
                strategy_folder_id = ensure_folder(drive, "01_Strategy", project_folder_id)
                if strategy_folder_id:
                    # 1. Create Google Doc from Markdown Deck
                    create_google_doc(drive, docs, f"Strategy Deck - {project_name}", strategy_folder_id, deck_content)
                    
                    # 2. Upload raw JSON data
                    upload_file(drive, str(strategy_dir / "brand_dna.json"), strategy_folder_id)
                    
                    logger.log("Strategist", "Strategy Deck and DNA mirrored to Google Drive.")
        except Exception as drive_err:
            logger.log("Strategist", f"Drive mirroring failed: {drive_err}", severity="WARN")

    except Exception as e:
        print(f"Error in Strategy Agent: {e}")
        brand_dna = {"error": str(e)}
        
    return {"brand_dna_json": brand_dna}
