import os
import json
from src.shared.db import create_db_and_tables, Project, Session, engine, ProjectOS

def verify_v12():
    print("--- [Verification] Templo Atelier v12.0: Founder Cockpit Stress Test ---\n")
    
    # 1. Reset Environment
    if os.path.exists("studio.db"): os.remove("studio.db")
    create_db_and_tables()
    
    # 2. Seed Data (Multi-Project Portfolio)
    with Session(engine) as session:
        # Project A: Active branding
        p1 = Project(
            name="Maldonado Club",
            client_brief="Luxury branding",
            budget_cap=5000.0,
            budget_spent=1200.0,
            internal_margin=65.0,
            internal_cost=1800.0,
            stage="Design",
            status="Strategy Finalized",
            health_score=95
        )
        # Project B: Incubating Lead
        p2 = Project(
            name="Eco-Resort 2026",
            client_brief="Sustainability strategy",
            budget_cap=3000.0,
            budget_spent=0.0,
            internal_margin=0.0,
            internal_cost=0.0,
            stage="Strategy",
            status="Brief Analysis",
            is_lead=True,
            health_score=100
        )
        # Project C: Delivery stage
        p3 = Project(
            name="TechConf Keynote",
            client_brief="Motion graphics for keynote",
            budget_cap=8000.0,
            budget_spent=4500.0,
            internal_margin=42.0,
            internal_cost=4600.0,
            stage="Delivery",
            status="Asset Export",
            health_score=80
        )
        session.add_all([p1, p2, p3])
        session.commit()

    print("✅ Seeded Project Portfolio (3 Projects).")

    # 3. Test Agent Translation
    print("\n--- Testing Founder Language Translation ---")
    # Simulate a Researcher status update
    ProjectOS.update_status(1, "Researcher", "Market Audit Synthesized.")
    
    with Session(engine) as session:
        p1 = session.get(Project, 1)
        print(f"Researcher Result: {p1.status}")
        if p1.status == "Market Intelligence Report Generated.":
            print("✅ Success: Technical status translated to Founder language.")
        else:
            print("❌ Failure: Status not translated.")

    # 4. Test Global Aggregation (Simulated Dashboard Logic)
    with Session(engine) as session:
        from sqlmodel import select
        projects = session.exec(select(Project)).all()
        
        active_count = len([p for p in projects if not p.is_lead])
        pipeline_vol = sum(p.budget_cap for p in projects)
        avg_margin = sum(p.internal_margin for p in projects) / len(projects)
        
        print(f"\n--- Global Metrics Check ---")
        print(f"Active Count: {active_count} (Expected: 2)")
        print(f"Pipeline Volume: ${pipeline_vol} (Expected: $16000.0)")
        print(f"Average Margin: {avg_margin:.1f}% (Expected: 35.7%)")
        
        if active_count == 2 and pipeline_vol == 16000.0:
            print("✅ Success: Global Cockpit metrics aggregated correctly.")
        else:
            print("❌ Failure: Metric mismatch.")

    print("\n--- v12.0 Verification Complete ---")

if __name__ == "__main__":
    verify_v12()
