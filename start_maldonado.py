import sys
import os
sys.path.insert(0, os.getcwd())

from src.operative_core.intake import IntakeAgent # type: ignore
from src.studio import run_studio_pipeline # type: ignore
from dotenv import load_dotenv # type: ignore
load_dotenv()

def start_maldonado():
    print("--- [Production] Templo Atelier: Initiating Maldonado Club ---")
    
    raw_input = "branding of maldonado club, luxury hospitality, inspired in soho house"
    
    intake = IntakeAgent()
    
    # 1. Analyze Input
    print(f"\n[UIA] Analyzing: '{raw_input}'")
    context = intake.analyze_input(raw_input)
    
    # 2. Scaffold & Initial Drive Mirroring
    print(f"\n[UIA] Scaffolding workspace for {context.project_name}...")
    intake.process_project(context)
    
    # 3. Trigger Full Pipeline (Audit -> Research -> Strategy -> Synthesis)
    print(f"\n[UIA] Triggering Agency Pipeline...")
    run_studio_pipeline(
        brief=context.model_dump_json(),
        budget=25000.0, # High-end hospitality baseline
        project_name=context.project_name,
        methodology="DEEP_DIVE_BRANDING",
        clarifying_questions=context.clarifying_questions
    )
    
    print("\n--- Project Staged for Director Review ---")

if __name__ == "__main__":
    start_maldonado()
