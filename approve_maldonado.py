import sys
import os
sys.path.insert(0, os.getcwd())

from src.shared.db import Project, Session, engine # type: ignore
from src.studio import run_studio_pipeline # type: ignore
from sqlmodel import select # type: ignore
from dotenv import load_dotenv # type: ignore
load_dotenv()

def approve_and_run_maldonado():
    print("--- [Production] Templo Atelier: Approving Maldonado Club ---")
    
    with Session(engine) as session:
        # Find the project
        statement = select(Project).where(Project.name == "Maldonado Club Branding")
        project = session.exec(statement).first()
        
        if not project:
            print("❌ Project 'Maldonado Club Branding' not found.")
            return
            
        print(f"✅ Found Project ID: {project.id}. Updating status to APPROVED.")
        project.review_status = "APPROVED"
        session.add(project)
        session.commit()
        
        # Trigger the pipeline again
        print(f"\n[ORCHESTRATOR] Resuming pipeline for {project.name}...")
        
        # We pass the existing brief and data. The pipeline will now pass the review gate.
        run_studio_pipeline(
            brief=project.client_brief,
            budget=project.budget_cap,
            project_name=project.name,
            methodology="DEEP_DIVE_BRANDING",
            project_id=project.id
        )

if __name__ == "__main__":
    approve_and_run_maldonado()
