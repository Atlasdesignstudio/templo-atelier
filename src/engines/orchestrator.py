from typing import List, Dict, Callable, Any, Set
from pydantic import BaseModel, Field
import time
import logging

logger = logging.getLogger("orchestrator")

# --- Context State ---
class WorkflowState(BaseModel):
    """
    Mutable state passed through the DAG.
    Holds artifacts, constraints, and execution logs.
    """
    project_id: str
    constraints: Dict[str, Any] = {}
    artifacts: Dict[str, Any] = {}
    logs: List[str] = []
    failed_nodes: Set[str] = set()

    def log(self, message: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")

# --- Node Definition ---
class WorkflowNode(BaseModel):
    id: str
    description: str
    dependencies: List[str] = []  # Node IDs this node waits for
    handler: Callable[[WorkflowState], Any]  # The function to execute
    
    # Validation
    required_state_keys: List[str] = []

# --- The Orchestrator ---
class OrchestrationEngine:
    def __init__(self):
        self.nodes: Dict[str, WorkflowNode] = {}
        self.executed: Set[str] = set()
    
    def register_node(self, node: WorkflowNode):
        self.nodes[node.id] = node

    def run(self, initial_state: WorkflowState) -> WorkflowState:
        """
        Executes the DAG until completion or deadlock.
        """
        initial_state.log("Starting Workflow Execution...")
        
        while len(self.executed) < len(self.nodes):
            executable = self._get_executable_nodes()
            
            if not executable:
                if len(self.executed) < len(self.nodes):
                    initial_state.log("Deadlock detected or dependencies incomplete.")
                    # In a real system, check for 'failed' nodes blocking paths
                break
            
            for node_id in executable:
                node = self.nodes[node_id]
                try:
                    initial_state.log(f"Executing Node: {node.id}")
                    # Prepare inputs if needed? For now, pass state.
                    result = node.handler(initial_state)
                    
                    # Store result if it's significant?
                    # Handler should mutate state.artifacts directly.
                    
                    initial_state.log(f"Node {node.id} Completed.")
                    self.executed.add(node_id)
                except Exception as e:
                    logger.error(f"Node {node_id} Failed: {e}")
                    initial_state.failed_nodes.add(node_id)
                    initial_state.log(f"ERROR: Node {node_id} failed: {e}")
                    # Determine retry logic here (Phase 1 Stub)
                    return initial_state  # Stop on failure for now
        
        initial_state.log("Workflow Execution Finished.")
        return initial_state

    def _get_executable_nodes(self) -> List[str]:
        candidates = []
        for node_id, node in self.nodes.items():
            if node_id in self.executed:
                continue
            
            # Check dependencies
            deps_met = all(dep in self.executed for dep in node.dependencies)
            if deps_met:
                candidates.append(node_id)
        return candidates
