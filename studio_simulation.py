import json
import time
from datetime import datetime, timedelta
from src.shared.db import create_db_and_tables, Project, Session, engine, ProjectOS, CalendarEvent, GlobalTask

def seed_studio_lifecycle():
    print("--- [Simulator] Seeding Studio Life-Cycle (Founder Cockpit v12.1) ---")
    
    # 1. Reset Environment
    create_db_and_tables()
    
    with Session(engine) as session:
        # 2. Seed Calendar
        now = datetime.utcnow()
        events = [
            CalendarEvent(title="Vanguard Contract Review", start_time=now + timedelta(hours=1), end_time=now + timedelta(hours=2), location="Zoom", is_critical=True),
            CalendarEvent(title="Alpha Design Sprint", start_time=now + timedelta(hours=4), end_time=now + timedelta(hours=5), location="Studio Boardroom"),
            CalendarEvent(title="New Lead: Ocean Pulse", start_time=now + timedelta(days=1, hours=2), end_time=now + timedelta(days=1, hours=3), location="Google Meet")
        ]
        
        # 3. Seed Global Tasks
        tasks = [
            GlobalTask(title="Submit Q1 Tax Report", due_date=now + timedelta(days=3), priority="High"),
            GlobalTask(title="Update Studio Brand DNA", due_date=now + timedelta(days=7), priority="Normal"),
            GlobalTask(title="Review Chief OS Audit", due_date=now + timedelta(hours=6), priority="Normal")
        ]
        
        # 4. Seed Multi-Stage Projects
        projects = [
            Project(
                name="Vanguard Rebrand",
                client_brief="Cyber-security branding pass.",
                budget_cap=12000.0,
                internal_margin=45.0,
                internal_cost=6500.0,
                stage="Design",
                status="Strategic Guardrail Alignment in progress.",
                health_score=88,
                next_milestone="Asset Selection",
                executive_summary="Targeting high-trust obsidian aesthetics for the security sector."
            ),
            Project(
                name="Neon Dream Campaign",
                client_brief="Retro-synth aesthetic for social assets.",
                budget_cap=4500.0,
                internal_margin=22.0,
                internal_cost=3200.0,
                stage="Delivery",
                status="Intelligence gathering complete.",
                health_score=42,
                next_milestone="Final Export",
                blocker_summary="Low margin alert: Review scope drift.",
                review_status="PENDING"
            ),
            Project(
                name="Siren Audio Identity",
                client_brief="Sonic branding for automotive startup.",
                budget_cap=15000.0,
                internal_margin=55.0,
                internal_cost=2500.0,
                stage="Strategy",
                status="Brand DNA & Positioning drafted.",
                health_score=99,
                next_milestone="Intelligence Review"
            )
        ]
        
        session.add_all(events)
        session.add_all(tasks)
        session.add_all(projects)
        session.commit()
    
    print("✅ Studio Heartbeat Seeding Complete.")

def simulate_live_updates():
    print("\n--- [Simulator] Starting Live Intelligence Pulse ---")
    try:
        # Simulate active agent intelligence flowing in
        research_snip = ["Market Gap: Emotional Resonance is missing in competitor A", "Trend: Hyper-minimalism is saturated"]
        ProjectOS.update_intelligence(3, "research", research_snip)
        ProjectOS.update_status(3, "Researcher", "Scanning market gaps and competitor landscape...")
        
        time.sleep(2)
        print("Pulse: Agent Researcher pushing Market Intelligence...")
        
        strategy_snip = ["North Star: Speed as a Luxury", "Value Prop: Autonomous Elegance"]
        ProjectOS.update_intelligence(3, "strategy", strategy_snip)
        ProjectOS.update_status(3, "Strategist", "Strategic Guardrail Alignment in progress.")
        
        time.sleep(2)
        print("Pulse: Agent Strategist pushing Strategic Guardrails...")
        
        print("\n--- [Simulation Complete] Studio is now in high-fidelity steady state. ---")
        print("Check http://localhost:8000 to see the Founder Cockpit live.")

    except Exception as e:
        print(f"Simulation Error: {e}")

if __name__ == "__main__":
    seed_studio_lifecycle()
    simulate_live_updates()
