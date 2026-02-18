from src.shared.db import Session, engine, Project, create_db_and_tables
from datetime import datetime, timedelta

def initialize_naos():
    print("--- [Initialization] Launching NAOS Project ---")
    create_db_and_tables()
    
    with Session(engine) as session:
        # Check if project already exists to avoid duplicates
        existing = session.query(Project).filter(Project.name == "NAOS").first()
        if existing:
            print("Project NAOS already exists. Re-initializing...")
            session.delete(existing)
            session.commit()

        naos = Project(
            name="NAOS",
            client_brief="NAOS is a curated platform for intentional, real-world experiences — connecting trusted hosts with people seeking depth, beauty, and meaningful connection beyond the noise of traditional event platforms. It’s not built for mass nightlife or high-volume ticket sales, but for intimate gatherings rooted in ritual, creativity, wellness, and culture. Design-led and trust-driven, NAOS aims to become the infrastructure for modern, conscious community — a digital gateway to the 'inner temple' in physical space.",
            budget_cap=8500.0,
            is_lead=True,
            stage="Strategy",
            status="Project Initialized",
            next_milestone="Market Intelligence Audit",
            health_score=100
        )
        session.add(naos)
        session.commit()
        print(f"✅ NAOS Project seeded in DB with ID: {naos.id}")
        return naos.id

if __name__ == "__main__":
    initialize_naos()
