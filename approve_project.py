import sys
import os
from sqlmodel import Session, select, func  # type: ignore

# Add src to path
sys.path.insert(0, os.getcwd())

from src.shared.db import engine, Project  # type: ignore

def approve_project(project_name: str):
    with Session(engine) as session:
        statement = select(Project).where(Project.name == project_name)
        project = session.exec(statement).first()
        
        if not project:
            print(f"Project '{project_name}' not found.")
            return
            
        project.review_status = "APPROVED"
        session.add(project)
        session.commit()
        print(f"✅ Project '{project_name}' APPROVED. Design agents will start on the next poll.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python approve_project.py 'Project Name'")
    else:
        approve_project(sys.argv[1])
