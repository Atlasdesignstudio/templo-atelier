from src.shared.db import Session, engine, Project, Deliverable, Risk, Invoice, CalendarEvent, GlobalTask, Document, AgentRequest, create_db_and_tables
from datetime import datetime, timedelta
import os

def init_v15():
    print("--- [Founder OS v15.0] Initializing Project Command Center Data ---")
    
    # 1. Reset DB
    if os.path.exists("studio.db"):
        os.remove("studio.db")
        print("Existing database removed.")
    
    create_db_and_tables()
    print("New v15.0 Schema applied (Tensions, Principles, Scope Stability, Docs, Requests).")

    with Session(engine) as session:
        # --- SEED PROJECTS ---
        
        # 1. MALDONADO CLUB (Primary Test Case for Command Center)
        maldonado = Project(
            name="Maldonado Club",
            client_brief="High-end social club branding.",
            budget_cap=15000.0,
            status="Design Phase",
            review_status="APPROVED",
            stage="Design",
            is_lead=False,
            health_score=92,
            next_milestone="UI Handoff",
            deadline=datetime.utcnow() + timedelta(days=21),
            executive_summary="Visual assets approved. Moving to UI.",
            
            # v15.0 Command Center Metrics
            scope_stability="Drifting", # Testing Alert
            margin_trend="Down", # Testing Alert
            projected_revenue=18000.0,
            invoiced_total=9000.0,
            internal_cost=3200.0,
            internal_margin=64.4,

            # v15.0 Deep Strategy
            strategic_tensions='["Exclusivity vs Visibility", "Tradition vs Modernity", "Member Privacy vs Social Buzz"]',
            design_principles='["Radical Simplicity", "Tactile Digitalism", "Quiet Luxury"]',
            strategy_json='{"archetype": "The Ruler", "tone": "Sophisticated, Timeless, Assured", "pillars": ["Heritage", "Privacy", "Service"]}',
            research_insights_json='{"market_gap": "Oversaturated \'loud\' luxury.", "competitors": ["Soho House", "Annabel\'s"], "opportunity": "Digital-first private membership."}'
        )
        session.add(maldonado)
        session.commit()
        session.refresh(maldonado)
        
        # MALDONADO ARTIFACTS
        
        # Documents (Folder Structure) - CONFIRMING IMPORT FIX
        # Folder: Strategy
        session.add(Document(project_id=maldonado.id, name="Brand Positioning_v2.md", category="Strategy", doc_type="text", content="# Brand Positioning\n\nWe are positioning Maldonado as the 'Anti-Club'."))
        session.add(Document(project_id=maldonado.id, name="Competitor Analysis", category="Strategy", doc_type="link", url="https://drive.google.com/drive/folders/maldonado-research"))
        
        # Folder: Legal
        session.add(Document(project_id=maldonado.id, name="MSA_Signed.pdf", category="Legal", doc_type="file", url="/files/maldonado_msa.pdf"))
        
        # Folder: Production
        session.add(Document(project_id=maldonado.id, name="Shot List", category="Production", doc_type="text", content="- Establish shot: Exterior\n- Detail: Marble texture\n- Action: Pouring drink"))
        
        # Deliverables (Production)
        session.add(Deliverable(project_id=maldonado.id, title="Visual Identity System", status="Approved", due_date=datetime.utcnow() - timedelta(days=5), owner="Director"))
        session.add(Deliverable(project_id=maldonado.id, title="Member App UI", status="In Progress", due_date=datetime.utcnow() + timedelta(days=10), owner="Designer"))
        session.add(Deliverable(project_id=maldonado.id, title="Marketing Website", status="Pending", due_date=datetime.utcnow() + timedelta(days=20), owner="Dev Agent"))

        # Risks (Governance)
        session.add(Risk(project_id=maldonado.id, description="Scope creep on video assets", severity="Medium", category="Scope", status="Active"))
        session.add(Risk(project_id=maldonado.id, description="Member App API delays", severity="High", category="Timeline", status="Active"))

        # Invoices (Financials)
        session.add(Invoice(project_id=maldonado.id, amount=9000.0, status="Paid", due_date=datetime.utcnow() - timedelta(days=15)))
        session.add(Invoice(project_id=maldonado.id, amount=9000.0, status="Draft", due_date=datetime.utcnow() + timedelta(days=15)))

        # Tasks (Action)
        session.add(GlobalTask(project_id=maldonado.id, title="Review App Wireframes", due_date=datetime.utcnow() + timedelta(days=1), priority="High", status="Todo"))
        session.add(GlobalTask(project_id=maldonado.id, title="Approve Video Budget", due_date=datetime.utcnow() + timedelta(days=2), priority="Medium", status="Todo"))
        session.add(GlobalTask(project_id=maldonado.id, title="Sync with Dev Team", due_date=datetime.utcnow() + timedelta(days=3), priority="Normal", status="Todo"))
        
        # Agent Requests (Founder Action)
        session.add(AgentRequest(project_id=maldonado.id, target_agent="CFO", request="Re-calculate burn rate with new video budget.", status="Pending"))
        session.add(AgentRequest(project_id=maldonado.id, target_agent="Strategist", request="Find 3 more benchmarks for 'Quiet Luxury' apps.", status="Completed", response="Added: The Row, Aman, Aesop."))

        # 2. NAOS (Secondary)
        naos = Project(
            name="NAOS",
            status="Strategy",
            stage="Strategy",
            health_score=85,
            projected_revenue=12000.0,
            invoiced_total=4250.0,
            client_brief="Conscious nightlife platform.",
            budget_cap=8500.0
        )
        session.add(naos)
        
        session.commit()
        print("✅ v15.0 Data Seeded: Maldonado Club (Full Context) & NAOS.")

if __name__ == "__main__":
    init_v15()
