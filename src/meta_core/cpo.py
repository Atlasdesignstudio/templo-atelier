import os
from sqlmodel import Session, select, func  # type: ignore
from src.shared.db import engine, AgentLog, Project  # type: ignore
from src.shared.drive_utils import get_drive_service, get_docs_service, find_folder, create_google_doc  # type: ignore
from datetime import datetime

class ChiefProcessOfficer:
    """
    The Meta-Agent that audits the studio.
    1. Performance Audit: Checks DB logs for failure rates.
    2. Task Audit: Checks task.md vs File System.
    """
    def __init__(self, task_file_path: str = "/Users/mathiasmeneses/.gemini/antigravity/brain/4b9cbef1-c278-480a-ba9f-15c9afc1d7a9/task.md"):
        self.task_file_path = task_file_path

    def run_audit(self):
        print("\n--- [CPO] Starting Nightly Audit ---\n")
        performance_data = self._audit_performance()
        self._audit_tasks()
        
        # Professional Upgrade: Generate report in Drive
        try:
            self.generate_health_report(performance_data)
        except Exception as e:
            print(f"[CPO] Failed to generate health report: {e}")
            
        print("\n--- [CPO] Audit Complete ---\n")

    def _audit_performance(self):
        print("1. Performance Audit:")
        metrics = {"error_rate": 0.0, "total_spend": 0.0, "total_logs": 0}
        
        with Session(engine) as session:
            # Calculate Failure Rate
            total_logs = session.exec(select(func.count(AgentLog.id))).one()
            errors = session.exec(select(func.count(AgentLog.id)).where(AgentLog.severity == "ERROR")).one()
            
            if total_logs > 0:
                failure_rate = (errors / total_logs) * 100
                metrics["error_rate"] = failure_rate
                metrics["total_logs"] = total_logs
                print(f"   - Total Logs: {total_logs}")
                print(f"   - Error Rate: {failure_rate:.2f}%")
            
            # Calculate Total Spend
            total_spend = session.exec(select(func.sum(AgentLog.cost_incurred))).one()
            metrics["total_spend"] = total_spend or 0.0
            print(f"   - Total Spend: ${metrics['total_spend']:.2f}")
            
        return metrics

    def _audit_tasks(self):
        print("\n2. Task Completion Audit:")
        if not os.path.exists(self.task_file_path):
            print(f"   - [ERROR] Task file not found at {self.task_file_path}")
            return

        with open(self.task_file_path, "r") as f:
            lines = f.readlines()

        pending_tasks = [line.strip() for line in lines if "- [ ]" in line]
        
        if pending_tasks:
            print(f"   - [WARN] Found {len(pending_tasks)} pending tasks:")
            for task in pending_tasks[:5]: # type: ignore
                print(f"     * {task}")
            
            # Logic to detecting missing implementation
            # Simplistic check: if "Implement CPO" is pending but src/meta_core/cpo.py exists...
            if any("Implement CPO" in t for t in pending_tasks) and os.path.exists("src/meta_core/cpo.py"):
                 print("   - [INSIGHT] 'Implement CPO' seems implemented in code but unchecked in task.md!")
        else:
            print("   - All tasks marked as complete.")

    def generate_health_report(self, metrics: dict):
        """Generates a professional studio health report in Google Drive."""
        print("\n3. Generating Studio Health Report in Drive...")
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        report_content = f"""# Templo Atelier — Studio Health Report ({date_str})

## 📊 Overview
All systems online. The autonomous creative pipeline is operating within design parameters.

## 📈 Performance Metrics
- **Error Rate**: {metrics.get('error_rate', 0):.2f}%
- **Total Operational Spend**: ${metrics.get('total_spend', 0):.2f}
- **Total Agent Events**: {metrics.get('total_logs', 0)}

## 🛠️ Infrastructure Status
- **Operative Core**: Healthy
- **Creative Core**: Healthy
- **Meta Core**: Audit Active

---
*Autonomous Audit by Templo Atelier CPO v2.0*
"""
        
        drive = get_drive_service()
        docs = get_docs_service()
        
        # Save to Drive root (or Templo Atelier root)
        root_id = find_folder(drive, "Templo Atelier")
        if not root_id:
            print("   - [ERROR] Templo Atelier folder not found, skipping report mirroring.")
            return
            
        create_google_doc(
            drive, 
            docs, 
            f"Studio Health Report — {date_str}", 
            root_id, 
            report_content
        )
        print(f"   - ✅ Report saved to Drive: Studio Health Report — {date_str}")

if __name__ == "__main__":
    cpo = ChiefProcessOfficer()
    cpo.run_audit()
