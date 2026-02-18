import os
import json
import time
from pathlib import Path
from src.studio import run_studio_pipeline
from src.shared.db import create_db_and_tables, Project, Session, engine
from src.shared.state_store import StateStore
from src.meta_core.architect import chief_architect

def verify_v11():
    print("--- [Verification] Templo Atelier v11.0: Production Stress Test ---")
    
    # 0. Setup
    create_db_and_tables()
    
    # --- TEST 1: Financial Lock ---
    print("\n[Test 1] Financial Lock Verification")
    low_budget_brief = "Branding for TEMPLO"
    result = run_studio_pipeline(low_budget_brief, budget=50.0, project_name="LowBudget_Test") # 50 is below threshold
    if result and result.get("error") == "FINANCIAL_LOCK_ACTIVE":
        print("✅ Success: Financial Lock prevented execution for insufficient funds.")
    else:
        print("❌ Failure: Financial Lock did not engage.")

    # --- TEST 2: Resumability (The Black Box) ---
    print("\n[Test 2] Resumability Verification")
    project_name = "Resumability_Test"
    brief = "Luxury wellness branding"
    
    # 1. Start project
    print("[OS] Starting initial run...")
    # We pass args in correct order: brief, budget, project_name
    run_studio_pipeline(brief, 100000.0, project_name)
    
    with Session(engine) as session:
        project = session.query(Project).filter(Project.name == project_name).first()
        if project and project.raw_state_json:
            print(f"✅ Success: Initial run saved atomic state checkpoint (raw_state_json exists).")
            
            # 2. Simulate Resume
            print("[OS] Simulating resume from Black Box...")
            res_state = StateStore.load_checkpoint(project.id)
            if res_state and res_state.get("project_id") == project.id:
                 print("✅ Success: StateStore correctly re-hydrated the project context.")
            else:
                 print("❌ Failure: StateStore could not load checkpoint.")
        else:
            print("❌ Failure: Project did not save atomic state.")

    # --- TEST 3: Meta-Agent Audit ---
    print("\n[Test 3] Meta-Agent Audit Verification")
    proposal = chief_architect.run_nightly_audit()
    if proposal and "# System Audit" in proposal:
        print("✅ Success: Chief OS Architect generated a System Optimization Report.")
        # Check if file exists
        report_dir = Path("storage/system/audit")
        reports = list(report_dir.glob("audit_*.md"))
        if len(reports) > 0:
            print(f"✅ Success: Report persisted to disk: {reports[0]}")
    else:
        print("❌ Failure: Chief OS Architect failed to generate report.")

    print("\n--- v11.0 Verification Complete ---")

if __name__ == "__main__":
    verify_v11()
