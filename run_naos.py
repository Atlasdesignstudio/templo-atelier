from src.studio import run_studio_pipeline
import sys

def execute_naos():
    project_id = 7
    budget = 8500.0
    print(f"--- [Execution] Triggering Agent Chain for Project {project_id} (NAOS) ---")
    result = run_studio_pipeline(brief="", budget=budget, project_id=project_id)
    print(f"--- [Execution Complete] Result: {result} ---")

if __name__ == "__main__":
    execute_naos()
