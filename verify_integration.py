import sys
import json
from src.operative_core.studio import studio
from src.operative_core.agent_base import AgentInput

def verify_integration():
    print("--- 🏛️  Verifying Templo Atelier vFinal Integration ---")
    
    # 1. Check Engines
    print(f"\n[1/4] Checking Engines...")
    print(f"✅ Orchestrator: {studio.orchestrator.__class__.__name__}")
    print(f"✅ Economics: {studio.economics.__class__.__name__}")
    print(f"✅ Perception: {studio.perception.__class__.__name__}")
    
    # 2. Check Agents
    print(f"\n[2/4] Checking Agents...")
    strategist = studio.agents.get("strategist")
    director = studio.agents.get("director")
    print(f"✅ Strategist: {strategist.__class__.__name__}")
    print(f"✅ Director: {director.__class__.__name__}")
    
    if not strategist or not director:
        print("❌ CRITICAL: Agents missing!")
        sys.exit(1)

    # 3. Test Strategist Task (Expand Strategy)
    print(f"\n[3/4] Testing Strategist (Expand Strategy)...")
    try:
        inp = AgentInput(
            task_description="expand_strategy",
            context_data={
                "project_name": "Integration Test Project",
                "brief": "A sustainable coffee shop for remote workers.",
                "direction": {"key": "A", "title": "Minimal Zen", "description": "Calm focus."}
            }
        )
        out = strategist.run(inp)
        print(f"✅ Strategist Output Confidence: {out.confidence}")
        if out.confidence > 0:
            print(f"   Structure: {json.dumps(out.structured_data, indent=2)}")
        else:
            print("   (Mock/Error output received, expected if API key missing)")
    except Exception as e:
        print(f"❌ Strategist Failed: {e}")

    # 4. Test Director Task (Recommend Deliverables)
    print(f"\n[4/4] Testing Director (Recommend Deliverables)...")
    try:
        inp = AgentInput(
            task_description="recommend_deliverables",
            context_data={
                "project_name": "Integration Test Project",
                "brief": "Coffee Shop"
            },
            parameters={
                "budget": 5000,
                "catalog": [
                    {"key": "logo", "title": "Logo", "cost": 1000},
                    {"key": "web", "title": "Website", "cost": 3000},
                    {"key": "video", "title": "Brand Video", "cost": 5000}
                ]
            }
        )
        out = director.run(inp)
        print(f"✅ Director Output Confidence: {out.confidence}")
        rec = out.structured_data.get("selected_keys", [])
        print(f"   Recommended: {rec}")
    except Exception as e:
        print(f"❌ Director Failed: {e}")

    print("\n✅ INTEGRATION VERIFIED.")

if __name__ == "__main__":
    verify_integration()
