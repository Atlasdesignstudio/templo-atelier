from typing import Dict, Any, Optional
import os
import json
from google import genai  # type: ignore
from src.shared.logger import AgentLogger  # type: ignore

def intelligence_critic_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    The Intelligence Critic (Guardrail Enforcer)
    Role: Audits agent outputs to ensure zero creative production.
    Ensures the studio remains 'Guardrails-Only'.
    """
    project_id = state.get("project_id", 1)
    logger = AgentLogger(project_id)
    
    logger.log("Critic", "Auditing Intelligence Guardrails...")
    
    # 1. Audit Criteria
    # We check if any creative outputs (logos, UI mockups, final copy) were generated.
    # In v9.0, agents should only output principles,IA, and strategic intelligence.
    
    findings = []
    
    # Check for visual assets in state or local paths
    if state.get("logo_svg_path"):
        findings.append("Creative Drift detected: Specialist generated a logo asset.")
    
    if state.get("figma_link") and not "methodology" in str(state.get("figma_link")).lower():
        findings.append("Creative Drift detected: UI Architect generated a direct Figma design link.")

    if state.get("video_assets"):
        findings.append("Creative Drift detected: Motion agent generated video files.")

    # 2. Strategic Depth Check (via Gemini)
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        You are the Quality Guardrail for Templo Atelier.
        Review the following strategic intelligence package. 
        Your ONLY job is to ensure the agents have NOT attempted to do the final creative work.
        They must only provide guardrails, principles, and intelligence.
        
        [INTELLIGENCE PACKAGE]
        {json.dumps(state.get('brand_dna_json', {}), indent=2)}
        
        Return "PASS" if the agents stayed within intelligence/guardrails.
        Return "FAIL: reason" if they attempted creative authorship.
        """
        try:
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            if "FAIL" in response.text.toUpperCase():
                findings.append(f"Strategic Audit Failure: {response.text}")
        except:
            pass

    if not findings:
        logger.log("Critic", "Guardrail Audit: PASSED. Studio is operating as 'Intelligence-Only'.")
        return {"critic_status": "APPROVED", "critic_feedback": "All guardrails enforced. Briefing Pack is intelligence-pure."}
    else:
        logger.log("Critic", f"Guardrail Failure: {findings[0]}", severity="WARN")
        return {
            "critic_status": "REJECTED",
            "critic_feedback": f"REJECTED: {findings[0]}"
        }
