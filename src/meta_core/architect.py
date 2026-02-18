import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from google import genai # type: ignore
from src.shared.db import Project, AgentLog, Session, engine
from pathlib import Path

class OSArchitect:
    """
    Chief OS Architect (Meta-Agent).
    Stands outside the project loops to audit and optimize the entire studio.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def run_nightly_audit(self) -> str:
        """Performs a comprehensive system audit across all projects."""
        print("--- [Meta-Agent] Chief OS Architect: Starting Nightly Audit ---")
        
        with Session(engine) as session:
            # 1. Gather Data
            projects = session.query(Project).all()
            logs = session.query(AgentLog).filter(AgentLog.timestamp > datetime.utcnow() - timedelta(days=7)).all()
            
            # 2. Analyze Bottlenecks & Margin
            audit_data = self._compile_audit_data(projects, logs)
            
            # 3. Generate Strategic Proposals (Gemini)
            if not self.client:
                print("!! NO API KEY !! Audit Report generated in manual mode.")
                proposal = "# System Audit (Manual)\n\nNo API Key found. Manual audit required."
            else:
                prompt = f"""
                You are the Chief OS Architect of Templo Atelier. 
                Review the following system performance data from the last 7 days.
                
                System Data: {json.dumps(audit_data, indent=2)}
                
                YOUR TASK:
                1. Detect Margin Erosion: Are we spending too many tokens on low-value projects?
                2. Detect Agent Bottlenecks: Which agents have the highest 'cycle_count' (rejects)?
                3. Detect Inefficiencies: Are there redundant steps?
                
                Return a 'System Optimization Proposal' in Markdown.
                Include:
                - Executive Sentiment (System Health %)
                - Critical Bottlenecks
                - Proposed Workflow Tweaks
                - Proposed Prompt Refinements (Specific suggestions)
                """
                
                try:
                    response = self.client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt,
                    )
                    proposal = response.text
                except Exception as e:
                    proposal = f"# Audit Failure\n\nAI Analysis failed: {e}"
            
            # 4. Save Proposal to Drive/Storage
            report_path = Path("storage/system/audit") / f"audit_{datetime.now().strftime('%Y-%m-%d')}.md"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w") as f:
                f.write(proposal)
                
            print(f"✅ Nightly Audit Complete. Report saved to {report_path}")
            return proposal

    def _compile_audit_data(self, projects: List[Project], logs: List[AgentLog]) -> Dict[str, Any]:
        """Synthesizes raw DB records into actionable audit metrics."""
        data = {
            "total_active_projects": len([p for p in projects if p.status != "Completed"]),
            "average_margin": sum([p.budget_cap - p.budget_spent for p in projects]) / len(projects) if projects else 0,
            "agent_performance": {},
            "warnings": []
        }
        
        # Aggregate Agent performance
        perf: Dict[str, Dict[str, int]] = {}
        for log in logs:
            name = str(log.agent_name)
            if name not in perf:
                perf[name] = {"errors": 0, "logs": 0}
            
            perf[name]["logs"] += 1
            if log.severity == "ERROR":
                perf[name]["errors"] += 1
        
        data["agent_performance"] = perf
        return data

# Singleton Instance
chief_architect = OSArchitect()
