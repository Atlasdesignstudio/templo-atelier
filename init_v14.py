from src.shared.db import Session, engine, Project, Deliverable, Risk, Invoice, CalendarEvent, GlobalTask, create_db_and_tables
from datetime import datetime, timedelta
import os

def init_v14():
    print("--- [Founder OS v14.0] Initializing Deep Data Architecture ---")
    
    # 1. Reset DB
    if os.path.exists("studio.db"):
        os.remove("studio.db")
        print("Existing database removed.")
    
    create_db_and_tables()
    print("New v14.0 Schema applied (Deliverables, Risks, Invoices tables created).")

    with Session(engine) as session:
        # --- SEED PROJECTS ---
        
        # 1. NAOS (The Active Lead -> Strategy)
        naos = Project(
            name="NAOS",
            client_brief="Curated platform for intentional, real-world experiences. 'Inner Temple' needed.",
            budget_cap=8500.0,
            status="Executive Review",
            review_status="PENDING",
            stage="Strategy",
            is_lead=False, # Active Project now
            health_score=85,
            next_milestone="Strategy Sign-off",
            deadline=datetime.utcnow() + timedelta(days=14),
            executive_summary="Strategic Guardrails defined. Inner Temple concept ready for review.",
            blocker_summary="Awaiting Founder Strategy Approval",
            # v14 Financials
            projected_revenue=12000.0,
            invoiced_total=4250.0, # Deposit
            internal_cost=850.0,
            internal_margin=92.0,
            # Deep Content (Mocking the Agent Output)
            research_insights_json='{"market_gap": "Lack of spiritual-luxury hybrids in current ticketing.", "competitors": ["RA Guide", "Dice", "MindBody"], "opportunity": "White space for \'Conscious Nightlife\' aggregator."}',
            strategy_json='{"archetype": "The Magician", "tone": "Enigmatic, High-Frequency, Curated", "pillars": ["Intentionality", "Exclusivity", "Connection"]}'
        )
        session.add(naos)
        session.commit()
        session.refresh(naos)
        
        # NAOS DATA
        session.add(Deliverable(project_id=naos.id, title="Brand Strategy Deck", status="Review", due_date=datetime.utcnow() + timedelta(days=1), owner="Director"))
        session.add(Deliverable(project_id=naos.id, title="Visual Identity V1", status="Pending", due_date=datetime.utcnow() + timedelta(days=7), owner="Stylist"))
        session.add(Risk(project_id=naos.id, description="Timeline tight for launch event", severity="High", category="Timeline", status="Active"))
        session.add(Invoice(project_id=naos.id, amount=4250.0, status="Paid", due_date=datetime.utcnow() - timedelta(days=5)))
        session.add(Invoice(project_id=naos.id, amount=4250.0, status="Draft", due_date=datetime.utcnow() + timedelta(days=20)))

        # 2. Maldonado Club (Design Phase)
        maldonado = Project(
            name="Maldonado Club",
            client_brief="High-end social club branding.",
            budget_cap=15000.0,
            status="Asset Production",
            stage="Design",
            is_lead=False,
            health_score=92,
            next_milestone="UI Handoff",
            executive_summary="Visual assets approved. Moving to UI.",
            projected_revenue=18000.0,
            invoiced_total=9000.0,
            internal_cost=3200.0
        )
        session.add(maldonado)
        session.commit()
        session.refresh(maldonado) # Refresh to get ID
        
        session.add(Deliverable(project_id=maldonado.id, title="Social Media Kit", status="In Progress", due_date=datetime.utcnow() + timedelta(days=2), owner="Social Agent"))
        session.add(Risk(project_id=maldonado.id, description="Scope creep on video assets", severity="Medium", category="Scope", status="Active"))
        session.add(Invoice(project_id=maldonado.id, amount=9000.0, status="Paid"))

        # 3. Eco-Resort 2026 (Lead)
        eco = Project(
            name="Eco-Resort 2026",
            client_brief="Sustainable luxury resort branding.",
            budget_cap=25000.0,
            status="Brief Analysis",
            stage="Lead",
            is_lead=True,
            health_score=100,
            next_milestone="Proposal Sent",
            projected_revenue=35000.0
        )
        session.add(eco)
        
        # 4. Neon Dream Campaign (Delivery)
        neon = Project(
            name="Neon Dream",
            client_brief="Cyberpunk fashion campaign.",
            budget_cap=5000.0,
            status="Final QA",
            stage="Delivery",
            is_lead=False,
            health_score=78,
            next_milestone="Launch",
            projected_revenue=6500.0,
            invoiced_total=6500.0,
            internal_cost=2100.0
        )
        session.add(neon)
        session.commit()
        session.refresh(neon)
        session.add(Deliverable(project_id=neon.id, title="Final Render Export", status="Pending", due_date=datetime.utcnow() + timedelta(hours=4), owner="Motion Agent"))
        session.add(Invoice(project_id=neon.id, amount=6500.0, status="Overdue", due_date=datetime.utcnow() - timedelta(days=2)))

        # GLOBAL TASKS
        session.add(GlobalTask(title="Approve Q1 Budget", due_date=datetime.utcnow() + timedelta(hours=2), priority="High", status="Todo"))
        session.add(GlobalTask(title="Review NAOS Strategy", due_date=datetime.utcnow() + timedelta(hours=5), priority="High", status="Todo", project_id=naos.id))

        session.commit()
        print("✅ v14.0 Data Seeded: NAOS, Maldonado, Eco-Resort, Neon Dream.")

if __name__ == "__main__":
    init_v14()
