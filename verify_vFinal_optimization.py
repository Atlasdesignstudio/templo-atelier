import sys
import logging
from src.engines.learning import LearningEngine, PreferenceNode
from src.engines.observability import ObservabilityEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_optimization")

def test_learning():
    print("\n[1/2] Testing Learning Engine...")
    try:
        learn = LearningEngine()
        
        # 1. Manually add preference (simulating extraction from feedback)
        pref = PreferenceNode(domain="Strategy", key="tone", value="Always minimize jargon.")
        learn.preferences.append(pref)
        
        # 2. Optimize Prompt
        base_prompt = "Generate a strategy for a coffee brand."
        optimized = learn.optimize_prompt(base_prompt, domain="Strategy")
        
        if "PREFER: Always minimize jargon." in optimized:
            print("✅ Preference Injection: Success.")
            print(f"Injection: {optimized.split('[Learned Preferences]:')[1].strip()}")
            return True
        else:
            print("❌ Preference Injection Failed.")
            return False
    except Exception as e:
        print(f"❌ Learning Error: {e}")
        return False

def test_observability():
    print("\n[2/2] Testing Observability Engine (Glass House)...")
    try:
        obs = ObservabilityEngine()
        proj = "proj_test_obs"
        
        # 1. Log Event
        obs.log_event(proj, "Director", "Decision Gate", {"option": "A"})
        
        # 2. Log Thought
        obs.log_thought(proj, "Strategist", "Thinking about cultural shifts...")
        obs.log_thought(proj, "Strategist", "Found shift: Digital Detox.")
        
        # 3. Retrieve Stream
        stream = obs.fetch_stream(proj)
        if len(stream) == 2 and "Digital Detox" in stream[1].content:
            print(f"✅ Thought Stream: Captured {len(stream)} thoughts.")
            return True
        else:
            print("❌ Thought Stream mismatch.")
            return False
            
    except Exception as e:
        print(f"❌ Observability Error: {e}")
        return False

if __name__ == "__main__":
    print("--- 🏛️  Verifying Templo Atelier Phase 4 (Optimization) ---")
    results = [test_learning(), test_observability()]
    
    if all(results):
        print("\n✅ OPTIMIZATION ENGINES ACTIVE.")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED.")
        sys.exit(1)
