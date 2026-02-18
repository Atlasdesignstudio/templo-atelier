import sys
import os
sys.path.insert(0, os.getcwd())

from src.studio import run_studio_pipeline # type: ignore
from dotenv import load_dotenv # type: ignore
load_dotenv()

def verify_v4():
    print("--- [Verification] Templo Atelier v4.0: Critic Layer Test ---")
    
    # A complex brief with a potential for mismatch
    complex_brief = """
    Project: Orion Cybernetics
    Goal: Create a brand for a high-end defense robotics company.
    Aesthetics: 'Soft, pastel colors' and 'Friendly, bubbly shapes'.
    Target Audience: Global defense ministries.
    Budget: High.
    """
    
    # This should trigger the Critic because 'Soft pastels' contradict 'Defense robotics' 
    # for 'Global defense ministries' (Strategic misalignment).
    
    result = run_studio_pipeline(
        brief=complex_brief,
        budget=5000.0,
        project_name="Orion Cybernetics",
        methodology="DEEP_DIVE_BRANDING"
    )
    
    print("\n--- [V4 Result] ---")
    print(f"Cycle Count: {result.get('cycle_count')}")
    print(f"Final Critic Feedback: {result.get('critic_feedback')}")
    
    if result.get('cycle_count', 0) > 1:
        print("✅ SUCCESS: Critic triggered a refinement cycle.")
    else:
        print("ℹ️ INFO: Strategy passed on the first try (or Critic was too lenient).")

if __name__ == "__main__":
    verify_v4()
