from typing import Dict, Any
from pathlib import Path
from src.shared.bank import StudioBank, COST_TABLE # type: ignore
from src.shared.logger import AgentLogger # type: ignore
from src.shared.db import ProjectOS # type: ignore

def visual_stylist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Design Intelligence Agent
    Role: Sets visual guardrails and evaluation criteria.
    Supports the human creative lead by providing exploration prompts.
    """
    project_id = state.get("project_id", 1)
    logger = AgentLogger(project_id)
    
    logger.log("Visual Stylist", "Establishing Visual Guardrails...")
    
    # 1. Budget check for intelligence extraction
    budget = state.get("project_budget_tokens", 0)
    bank = StudioBank(budget)
    cost = COST_TABLE["image_flux_pro"] # Symbolic cost for "Design Intelligence"
    
    if not bank.check_funds(cost):
        return {"project_status": "Paused: Budget Exceeded"}
    
    # 2. Logic: Define Guardrails
    project_name = state.get("project_name", "Untitled")
    safe_name = project_name.replace(" ", "_").replace("/", "-")
    proj_root = Path("projects") / "2026" / safe_name
    design_dir = proj_root / "02_Design"
    design_dir.mkdir(parents=True, exist_ok=True)
    
    # Intelligence Synthesis
    design_intel = {
        "visual_guardrails": [
            "Maintain high-contrast sophistication",
            "Avoid literal industry cliches",
            "Focus on 'Quiet Luxury' aesthetics"
        ],
        "exploration_prompts": [
            "Explore serif-heavy typography with custom ligatures",
            "Experiment with monochrome palette + 1 metallic accent",
            "Consider negative space as a primary brand element"
        ],
        "eval_checklist": [
            "Does it feel timeless rather than trendy?",
            "Is the complexity appropriate for small-scale favicon use?",
            "Does it align with the 'Member-Only' strategic pillar?"
        ]
    }
    
    # Local Persistence
    intel_file = design_dir / "Design_Intelligence.md"
    content = f"""# Design Intelligence: {project_name}
    
## 🛡️ Visual Guardrails
- {"\n- ".join(design_intel['visual_guardrails'])}

## 🎨 Exploration Prompts (For You)
- {"\n- ".join(design_intel['exploration_prompts'])}

## ⚖️ Evaluation Checklist
Use this to judge your design concepts:
- {"\n- ".join(design_intel['eval_checklist'])}
"""
    with open(intel_file, "w") as f:
        f.write(content)
        
    logger.log("Visual Stylist", "Design guardrails established locally.", cost=cost)

    # --- Real-Time OS Sync ---
    ProjectOS.update_intelligence(project_id, "strategy", design_intel["visual_guardrails"]) # Map visual guardrails to strategy view
    ProjectOS.update_status(project_id, "Visual Stylist", "Visual Guardrails Established")

    new_budget = budget - cost

    # 3. Mirror to Drive
    try:
        from src.shared.drive_utils import get_drive_service, find_folder, ensure_folder, upload_file  # type: ignore
        drive = get_drive_service()
        root_id = find_folder(drive, "Templo Atelier")
        projects_id = find_folder(drive, "05_Projects", root_id)
        project_folder_id = find_folder(drive, project_name, projects_id)
        
        if project_folder_id:
            design_folder_id = ensure_folder(drive, "02_Design", project_folder_id)
            upload_file(drive, str(intel_file), design_folder_id)
            logger.log("Visual Stylist", "Design intelligence mirrored to Google Drive.")
    except Exception as e:
        logger.log("Visual Stylist", f"Drive sync failed: {e}", severity="WARN")

    return {
        "design_intel_path": str(intel_file),
        "project_budget_tokens": new_budget
    }
