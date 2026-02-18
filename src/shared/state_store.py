import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from src.shared.db import Project, Session, engine # type: ignore

logger = logging.getLogger(__name__)

class StateStore:
    """
    Persistent State Store (The Black Box).
    Ensures that every node transition in LangGraph is backed up to disk/DB.
    """
    
    @staticmethod
    def _is_jsonable(x):
        try:
            json.dumps(x)
            return True
        except:
            return False

    @staticmethod
    def save_checkpoint(project_id: int, node_name: str, state: Dict[str, Any]):
        """Saves a snapshot of the current state for a project at a specific node."""
        try:
            # 1. Prepare Serializable Snapshot (Exclude complex objects like Integrator)
            serializable_state = {}
            for k, v in state.items():
                if k == "integrator": continue # Skip the agent object
                try:
                    # Test serialization
                    json.dumps(v)
                    serializable_state[k] = v
                except (TypeError, OverflowError):
                    # If it's a dict, try to filter it
                    if isinstance(v, dict):
                        serializable_state[k] = {sk: sv for sk, sv in v.items() if self._is_jsonable(sv)} # type: ignore
                    continue
            
            snapshot = {
                "timestamp": datetime.utcnow().isoformat(),
                "node": node_name,
                "state": serializable_state
            }
            
            # 2. Local File Persistence (Redundancy)
            project_name = state.get("project_name", f"proj_{project_id}")
            safe_name = str(project_name).replace(" ", "_").replace("/", "-")
            checkpoint_dir = Path("storage/checkpoints") / safe_name
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            checkpoint_file = checkpoint_dir / f"latest.json"
            with open(checkpoint_file, "w") as f:
                json.dump(snapshot, f, indent=4)
                
            # 3. DB Persistence (Primary)
            with Session(engine) as session:
                project = session.get(Project, project_id)
                if project:
                    # Update status and pulse
                    project.active_agent = node_name
                    project.last_node = node_name
                    project.last_pulse = datetime.utcnow()
                    project.raw_state_json = json.dumps(serializable_state)
                    session.add(project)
                    session.commit()
                    
            logger.info(f"[StateStore] Checkpoint saved for project {project_id} at node '{node_name}'")
            
        except Exception as e:
            logger.error(f"[StateStore] Failed to save checkpoint: {e}")

    @staticmethod
    def load_checkpoint(project_id: int) -> Optional[Dict[str, Any]]:
        """Loads the latest state snapshot for a project."""
        try:
            with Session(engine) as session:
                project = session.get(Project, project_id)
                if not project:
                    return None
                    
                safe_name = str(project.name).replace(" ", "_").replace("/", "-")
                checkpoint_file = Path("storage/checkpoints") / safe_name / "latest.json"
                
                if checkpoint_file.exists():
                    with open(checkpoint_file, "r") as f:
                        data = json.load(f)
                        return data.get("state")
            return None
        except Exception as e:
            logger.error(f"[StateStore] Failed to load checkpoint: {e}")
            return None

    @staticmethod
    def audit_trail(project_id: int, message: str, agent: str = "System"):
        """Logs a high-integrity audit entry to the AgentLog table."""
        from src.shared.db import AgentLog # type: ignore
        with Session(engine) as session:
            log = AgentLog(
                project_id=project_id,
                agent_name=agent,
                message=message,
                severity="INFO"
            )
            session.add(log)
            session.commit()
