import os
import yaml  # type: ignore
import json
import io
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from google import genai  # type: ignore
from src.models import ProjectContext, Mission  # type: ignore
from src.operative_core.mission_control import ProjectScaffold, ProposalGenerator  # type: ignore
from src.shared.db import Project, Session, engine, create_db_and_tables  # type: ignore


# Shared Drive utilities
from src.shared.drive_utils import (  # type: ignore
    get_drive_service,
    get_docs_service,
    find_folder,
    ensure_folder,
    create_google_doc
)


class IntakeAgent:
    def __init__(self, trigger_path: str = "scenarios/intake_trigger"):
        create_db_and_tables()
        self.trigger_path = Path(trigger_path)
        self.scaffold = ProjectScaffold()
        self.proposal_gen = ProposalGenerator()
        
        # Ensure trigger directory exists
        self.trigger_path.mkdir(parents=True, exist_ok=True)

    def monitor_drive(self):
        """
        Checks for new files in the trigger directory.
        In a real scenario, this would be a webhook listener.
        """
        print(f"[{self.__class__.__name__}] Monitoring {self.trigger_path} for new transcripts...")
        files = list(self.trigger_path.glob("*"))
        if not files:
            print("No new transcripts found.")
            return

        for file in files:
            print(f"[{self.__class__.__name__}] Processing: {file.name}")
            content = file.read_text()
            
            # 1. Analyze
            context = self.analyze_input(content)
            
            # 2. Assign & Scaffold
            self.process_project(context)
            
            # Cleanup (Move to processed or delete)
            # file.unlink() # promoting non-destructive testing for now
            print(f"[{self.__class__.__name__}] Finished processing {file.name}")

    def analyze_input(self, text: str) -> ProjectContext:
        """
        Universal Intake Agent (UIA):
        Extracts structured context, detects missing info, and classifies the project.
        """
        print(f"[{self.__class__.__name__}] Extracting context with Gemini...")
        
        # Check for Key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
             print("!! NO API KEY FOUND !! Using Mock Fallback")
             return self._mock_analyze_input(text)
        
        # Init GenAI Client
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are the Universal Intake Agent at Templo Atelier.
        Extract the core project architecture from this input (Text, Brief, or Transcript).
        
        INPUT: {text}
        
        YOUR TASK:
        1. Classify the Project Type (Branding, UX, Social, Industrial, Strategy, or Hybrid).
        2. Extract Goals, Deliverables, and Deadlines.
        3. IDENTITY GAPS: What critical info is missing? (Budget? Timeline? Specific Scope?)
        4. If info is missing, generate 3 strategic clarifying questions.
        
        Return a JSON object only (no markdown formatting) with:
        - project_name: str
        - project_type: str
        - client_goals: list[str]
        - deliverables: list[str]
        - hard_deadlines: dict[str, str]
        - budget_hint: str
        - missing_info: list[str]
        - clarifying_questions: list[str] 
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
                
            data = json.loads(raw_text)
            return ProjectContext(**data)
        except Exception as e:
            print(f"Error in UIA Extraction: {e}")
            return self._mock_analyze_input(text)

    def _mock_analyze_input(self, text: str) -> ProjectContext:
        """
        Fallback mock logic for UIA.
        """
        return ProjectContext(
            project_name="New Project Initiation",
            project_type="Unknown",
            client_goals=["Extract from: " + text[:50]],  # type: ignore
            deliverables=["Pending analysis"],
            hard_deadlines={},
            budget_hint="TBD",
            missing_info=["Full scope analysis pending"],
            clarifying_questions=["What is the primary objective?", "What is the budget?", "What is the deadline?"]
        )

    def assign_missions(self, context: ProjectContext) -> Dict[str, Any]:
        """
        Maps deliverables to agents and determines methodology.
        """
        agents = set(["cfo", "researcher"]) # Core v3 OS agents
        
        # Methodology Detection
        methodology = "STANDARD_CREATIVE_STILL"
        deliverables_text = " ".join(context.deliverables).lower()
        
        if "web" in deliverables_text or "app" in deliverables_text:
            methodology = "INTERACTIVE_EXPERIENCE"
            agents.add("ui_ux")
        if "social" in deliverables_text:
            methodology = "SOCIAL_GROWTH_SPRINT"
            agents.add("social")
        if "brand" in deliverables_text or "identity" in deliverables_text:
            methodology = "DEEP_DIVE_BRANDING"
            agents.add("strategist")
            agents.add("stylist")
        
        return {
            "agents": list(agents),
            "methodology": methodology
        }

    def process_project(self, context: ProjectContext, budget: float = 1000.0):
        """
        Orchestrates the scaffolding and notification.
        """
        # 1. Determine Agents & Methodology
        assignments = self.assign_missions(context)
        active_agents = assignments["agents"]
        methodology = assignments["methodology"]
        
        # 2. Create Mission
        mission = Mission(
            name=f"Launch {context.project_name}",
            status="In Progress",
            completion=0.20, 
            active_agents=active_agents,
            next_step="Review Initial Proposal",
            context=context
        )
        
        # 3. Scaffold Structure
        print(f"[{self.__class__.__name__}] Scaffolding project: {context.project_name}")
        project_root = self.scaffold.create_structure(context)
        
        # 4. Inject Mission
        self.scaffold.inject_mission(project_root, mission)
        
        # 4. Database Record
        is_complete = len(context.missing_info) == 0
        review_status = "PENDING" if is_complete else "INCUBATING"
        
        with Session(engine) as session:
            project = Project(
                name=context.project_name, 
                client_brief=json.dumps(context.dict()), 
                budget_cap=budget,  # type: ignore
                status="Intake",
                review_status=review_status
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            project_id = project.id

        # 5. Generate Proposal
        print(f"[{self.__class__.__name__}] Generating proposal...")
        proposal_content = self.proposal_gen.generate(context)
        
        # Save Proposal to 00_Intake
        proposal_path = Path(project_root) / "00_Intake" / "Initial_Proposal.md"
        with open(proposal_path, "w") as f:
            f.write(proposal_content)
            
        print(f"[{self.__class__.__name__}] Project Initialized at {project_root}")
        
        # 6. Mirror to Google Drive
        try:
            self.mirror_to_drive(context, proposal_content)
        except Exception as e:
            print(f"[{self.__class__.__name__}] ⚠️ Drive Mirroring failed: {e}")

    def mirror_to_drive(self, context: ProjectContext, proposal_content: str):
        """
        Creates the project folder and subfolders in Google Drive, 
        and uploads the initial proposal as a Google Doc.
        """
        print(f"[{self.__class__.__name__}] Mirroring to Google Drive...")
        
        drive = get_drive_service()
        docs = get_docs_service()
        
        # 1. Locate Templo Atelier/05_Projects
        root_id = find_folder(drive, "Templo Atelier")
        if not root_id:
            raise RuntimeError("Root 'Templo Atelier' folder not found in Drive.")
            
        projects_id = ensure_folder(drive, "05_Projects", root_id)
        
        # 2. Create Project Folder
        project_folder_id = ensure_folder(drive, context.project_name, projects_id)
        
        # 3. Create Subfolders
        subfolders = ["00_Intake", "01_Strategy", "02_Design", "03_Finance", "99_Delivery"]
        subfolder_ids = {}
        for sf in subfolders:
            subfolder_ids[sf] = ensure_folder(drive, sf, project_folder_id)
            
        # 4. Create Initial Proposal Doc in 00_Intake
        create_google_doc(
            drive, 
            docs, 
            "Initial Proposal", 
            subfolder_ids["00_Intake"], 
            proposal_content
        )
        
        print(f"[{self.__class__.__name__}] ✅ Drive Mirroring Complete.")


if __name__ == "__main__":
    agent = IntakeAgent()
    agent.monitor_drive()
