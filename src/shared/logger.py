from .db import AgentLog, engine  # type: ignore
from sqlmodel import Session  # type: ignore

class AgentLogger:
    def __init__(self, project_id: int):
        self.project_id = project_id

    def log(self, agent_name: str, message: str, cost: float = 0.0, severity: str = "INFO"):
        with Session(engine) as session:
            log_entry = AgentLog(
                project_id=self.project_id,
                agent_name=agent_name,
                message=message,
                cost_incurred=cost,
                severity=severity
            )
            session.add(log_entry)
            session.commit()
            print(f"[{agent_name}] {message} (Cost: ${cost})")
