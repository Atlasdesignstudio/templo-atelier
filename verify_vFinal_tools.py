import sys
import logging
from datetime import datetime
from src.engines.economics import EconomicsEngine, Quote
from src.engines.perception import PerceptionEngine, Signal
from src.engines.tool_router import ToolRouter, ToolRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_tools")

def test_economics():
    print("\n[1/3] Testing Economics Engine...")
    try:
        eco = EconomicsEngine()
        proj = "proj_001"
        eco.set_budget(proj, 10.00) # $10
        
        # Log cost (1M * 2M tokens) -> Should be small but non-zero
        eco.log_cost(proj, "Strategist", "LLM", tokens_in=1000, tokens_out=500)
        
        if eco.check_budget(proj):
            print(f"✅ Budget Check: Pass (Remaining: ${eco.budgets[proj].remaining:.4f})")
        else:
            print("❌ Budget Check Failed unexpectedly.")
            return False
            
        quote = eco.generate_quote(proj, complexity_score=2)
        print(f"✅ Quote Generated: ${quote.estimated_cost}")
        return True
    except Exception as e:
        print(f"❌ Economics Error: {e}")
        return False

def test_perception():
    print("\n[2/3] Testing Perception Engine...")
    try:
        perc = PerceptionEngine()
        sig = Signal(
            domain="Tech", 
            signal_type="Trend", 
            entity="AI", 
            element="Agents", 
            observation="Agents replace apps."
        )
        perc.ingest_signal(sig)
        
        results = perc.query_reservoir("agents")
        if len(results) > 0:
            print(f"✅ Perception Query: Found {len(results)} signals.")
            return True
        else:
            print("❌ Perception Query: No results found.")
            return False
    except Exception as e:
        print(f"❌ Perception Error: {e}")
        return False

def test_tool_router():
    print("\n[3/3] Testing Tool Router...")
    try:
        router = ToolRouter()
        
        # Register custom mock if needed, but defaults are registered in __init__
        req = ToolRequest(
            tool_name="filesystem",
            action="write",
            params={"path": "test.txt", "content": "Hello"},
            requester_agent="Strategist"
        )
        res = router.route(req)
        
        if res.success:
            print(f"✅ Tool Call Success: {res.data}")
            return True
        else:
            print(f"❌ Tool Call Failed: {res.error}")
            return False
            
    except Exception as e:
        print(f"❌ Router Error: {e}")
        return False

if __name__ == "__main__":
    print("--- 🏛️  Verifying Templo Atelier vFinal Tools ---")
    results = [test_economics(), test_perception(), test_tool_router()]
    
    if all(results):
        print("\n✅ ALL ENGINES OPERATIONAL.")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED.")
        sys.exit(1)
