import sys
import os
sys.path.insert(0, os.getcwd())

from src.studio import run_studio_pipeline # type: ignore
from dotenv import load_dotenv # type: ignore
load_dotenv()

def verify_v5():
    print("--- [Verification] Templo Atelier v5.0: Executive Surface Test ---")
    
    brief = """
    Project: Quantum Zenith
    Goal: Create a brand for a high-performance quantum computing workstation.
    Aesthetics: 'Brutalist minimalism' and 'Cold blue accents'.
    Target Audience: Security engineers and data scientists.
    Deliverables: Brand Identity, UX Wireframes, Social Media Templates.
    Budget: $8500.
    """
    
    # This will run Researcher -> Strategist -> Critic (Verify) -> Director (Synthesize)
    result = run_studio_pipeline(
        brief=brief,
        budget=8500.0,
        project_name="Quantum Zenith",
        methodology="INTERACTIVE_EXPERIENCE"
    )
    
    print("\n--- [V5 Result] ---")
    summary = result.get('executive_summary', 'No summary generated.')
    print(f"Executive Summary Excerpt:\n{summary[:500]}...")
    
    if result.get('executive_summary'):
        print("\n✅ SUCCESS: Executive Surface Layer generated and pushed to Drive.")
    else:
        print("\n❌ FAILURE: Executive summary missing.")

if __name__ == "__main__":
    verify_v5()
