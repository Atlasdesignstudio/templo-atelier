from typing import Dict, Any
from src.shared.bank import StudioBank, COST_TABLE  # type: ignore
from src.shared.logger import AgentLogger  # type: ignore
from src.shared.drive_utils import get_drive_service, find_folder, ensure_folder, upload_file  # type: ignore
import json
from pathlib import Path

def cfo_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chief Financial Officer 
    Role: Calculates symbolic project margins and generates professional Quotations.
    """
    project_id = state.get("project_id", 1)
    project_name = state.get("project_name", "Unknown Project")
    logger = AgentLogger(project_id)
    
    logger.log("CFO", f"Generating Quotation for {project_name}...")
    
    # 1. Symbolic Margin Logic
    # We calculate the quote based on standard service prices from COST_TABLE
    from src.shared.db import Project, Session, engine  # type: ignore
    
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            return {"project_status": "Error"}

        # Determine services from context (simplfied for v3)
        services = []
        total_quote = 0.0
        
        brief_lower = project.client_brief.lower()
        if "brand" in brief_lower or "logo" in brief_lower:
            services.append(("Branding Package", COST_TABLE["service_branding_package"]))
        if "web" in brief_lower or "ui" in brief_lower:
            services.append(("Web UX Design", COST_TABLE["service_web_ux_design"]))
        if "social" in brief_lower:
            services.append(("Social Campaign", COST_TABLE["service_social_campaign"]))
        
        # Always add research fee in v3
        services.append(("Market Intelligence Audit", COST_TABLE["service_market_research"]))
        
        total_quote = sum(s[1] for s in services)
        
        # Internal Overhead (Symbolic)
        # Assuming 5 agents invoked during full run
        internal_cost = 5 * COST_TABLE["internal_agent_overhead"]
        margin = total_quote - internal_cost
        margin_percent = (margin / total_quote) * 100 if total_quote > 0 else 0

        # --- [Generation: Quotation.md] ---
        quote_md = f"""# Project Quotation: {project_name}
Date: 2026-02-17
Client ID: {project_id}

## Scope of Services
"""
        for name, price in services:
            quote_md += f"- **{name}**: ${price:.2f}\n"
            
        quote_md += f"""
---
### **Total Quotation: ${total_quote:.2f}**
*Proposed Timeline: 2-3 Weeks*

## Financial Health (Internal)
- Internal Estimated Effort: ${internal_cost:.2f}
- Projected Margin: {margin_percent:.2f}%
"""

        try:
            safe_name = project_name.replace(" ", "_")
            proj_root = Path("projects") / "2026" / safe_name
            finance_dir = proj_root / "03_Finance"
            finance_dir.mkdir(parents=True, exist_ok=True)
            
            # Save local MD and JSON
            quote_path = finance_dir / "Quotation.md"
            with open(quote_path, "w") as f:
                f.write(quote_md)
                
            finance_data = {
                "project_id": project_id,
                "total_quote": total_quote,
                "margin_percent": margin_percent,
                "services": dict(services)
            }
            with open(finance_dir / "Financial_Plan.json", "w") as f:
                json.dump(finance_data, f, indent=4)
            
            # Sync to Dashboard DB
            project.internal_margin = margin_percent
            project.internal_cost = internal_cost
            session.add(project)
            session.commit()
            
            # Mirror to Drive
            drive = get_drive_service()
            root_id = find_folder(drive, "Templo Atelier")
            projects_id = find_folder(drive, "05_Projects", root_id)
            project_folder_id = find_folder(drive, project_name, projects_id)
            
            if project_folder_id:
                finance_folder_id = ensure_folder(drive, "03_Finance", project_folder_id)
                upload_file(drive, str(quote_path), finance_folder_id)
                upload_file(drive, str(finance_dir / "Financial_Plan.json"), finance_folder_id)
                logger.log("CFO", "Quotation mirrored to Google Drive.")
        except Exception as e:
            logger.log("CFO", f"Financial generation failed: {e}", severity="ERROR")

    return {"project_status": "Quotation Generated"}
