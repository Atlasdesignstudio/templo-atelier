"""
Templo OS v16.0 — Clean Seed
Only NAOS with its real data. No demo projects.
"""
from src.shared.db import Session, engine, Project, Deliverable, Risk, Invoice, CalendarEvent, GlobalTask, Document, AgentRequest, WorkflowStep, create_db_and_tables
from datetime import datetime, timedelta
import os

def init_v16():
    print("--- [Templo OS v16.0] Clean Seed ---")

    # Reset DB
    if os.path.exists("studio.db"):
        os.remove("studio.db")
        print("Previous database removed.")

    create_db_and_tables()
    print("v16.0 schema applied.")

    with Session(engine) as session:
        # NAOS — Real project, minimal data.
        # Only what we actually know. The rest gets filled via the UI onboarding.
        naos = Project(
            name="NAOS",
            client_brief="Conscious nightlife platform.",
            budget_cap=8500.0,
            status="Strategy",
            stage="Strategy",
            is_lead=False,
            health_score=85,
            projected_revenue=12000.0,
            invoiced_total=4250.0,
            internal_cost=0.0,
            internal_margin=0.0,
        )
        session.add(naos)
        session.commit()
        print("✅ v16.0 Seeded: NAOS (real project, minimal data)")
        print("   → Use the New Project wizard in the UI to add details.")

if __name__ == "__main__":
    init_v16()
