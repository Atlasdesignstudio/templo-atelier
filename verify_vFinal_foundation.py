import sys
import logging
from src.operative_core.models.memory import KnowledgeVector, EntityNode, RegulationRule
from src.engines.governance import GovernanceEngine, QARubric
from src.engines.orchestrator import OrchestrationEngine, WorkflowNode, WorkflowState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_foundation")

def test_memory_models():
    print("\n[1/3] Testing Memory Models...")
    try:
        vec = KnowledgeVector(content="Test Doc", embedding="[0.1, 0.2]")
        node = EntityNode(name="Brand A", category="Competitor", attributes='{"risk": "high"}')
        rule = RegulationRule(domain="Finance", rule_content="Disclaim risks.")
        
        print(f"✅ Vector Created: {vec.content}")
        print(f"✅ Node Created: {node.name} ({node.category})")
        print(f"✅ Rule Created: {rule.domain}")
        return True
    except Exception as e:
        print(f"❌ Memory Model Error: {e}")
        return False

def test_governance():
    print("\n[2/3] Testing Governance Engine...")
    try:
        gov = GovernanceEngine()
        rubric = QARubric(name="Strict Check", min_score=8)
        gov.register_rubric("strict", rubric)
        
        # Test pass case
        report = gov.evaluate_artifact("This is a long enough artifact content string to pass the validation check.", "strict")
        if report.passed:
            print(f"✅ Governance PASS: Score {report.scores[0].score}")
        else:
            print(f"❌ Governance FAIL: {report.blocking_issues}")
            return False
            
        # Test fail case
        fail_report = gov.evaluate_artifact("Too short.", "strict")
        if not fail_report.passed:
            print(f"✅ Governance REJECT (Expected): {fail_report.blocking_issues}")
        else:
            print(f"❌ Governance FAIL: Expected rejection, got pass.")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Governance Error: {e}")
        return False

def test_orchestration():
    print("\n[3/3] Testing Orchestration Engine (DAG)...")
    try:
        orch = OrchestrationEngine()
        
        # Define Nodes
        node_a = WorkflowNode(
            id="A", description="Start", 
            handler=lambda s: s.artifacts.update({"A": "Done"})
        )
        
        node_b = WorkflowNode(
            id="B", description="Process", dependencies=["A"],
            handler=lambda s: s.artifacts.update({"B": s.artifacts["A"] + " -> Processed"})
        )
        
        node_c = WorkflowNode(
            id="C", description="Finish", dependencies=["B"],
            handler=lambda s: s.artifacts.update({"C": "Job Complete"})
        )
        
        orch.register_node(node_a)
        orch.register_node(node_b)
        orch.register_node(node_c)
        
        # Run
        state = WorkflowState(project_id="test_proj_001")
        final_state = orch.run(state)
        
        # Check Execution logic
        if "Job Complete" in final_state.artifacts.get("C", ""):
            print("✅ Orchestration SUCCESS: Full DAG executed.")
            print(f"Artifacts: {final_state.artifacts}")
            return True
        else:
            print("❌ Orchestration FAIL: DAG incomplete.")
            print(f"Logs: {final_state.logs}")
            return False
            
    except Exception as e:
        print(f"❌ Orchestrator Error: {e}")
        return False

if __name__ == "__main__":
    print("--- 🏛️  Verifying Templo Atelier vFinal Engines ---")
    results = [test_memory_models(), test_governance(), test_orchestration()]
    
    if all(results):
        print("\n✅ ALL SYSTEMS GREEN. Foundation Phase Complete.")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED.")
        sys.exit(1)
