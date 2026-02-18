from typing import List, Optional
from langgraph.graph import StateGraph, END  # type: ignore
from src.shared.state import StudioState  # type: ignore

# Operative Core
from src.operative_core.growth import growth_agent  # type: ignore
from src.operative_core.cfo import cfo_agent  # type: ignore

# Creative Core
from src.creative_core.strategist import strategy_agent  # type: ignore
from src.creative_core.stylist import visual_stylist_agent  # type: ignore
from src.creative_core.ui_ux import ui_architect_agent  # type: ignore
from src.creative_core.social import social_growth_agent  # type: ignore
from src.creative_core.packaging import packaging_agent  # type: ignore
from src.creative_core.motion import motion_choreographer_agent  # type: ignore
from src.creative_core.researcher import researcher_agent  # type: ignore
from src.meta_core.critic import intelligence_critic_agent  # type: ignore
from src.meta_core.director import director_agent  # type: ignore
from src.shared.state_store import StateStore # type: ignore
from src.meta_core.architect import chief_architect # type: ignore

import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate  # type: ignore
from langchain_core.output_parsers import JsonOutputParser  # type: ignore
from src.models import BrandDNA  # type: ignore

def _build_workflow():
    """Builds and compiles the LangGraph workflow. Reusable across entrypoints."""
    workflow = StateGraph(StudioState)
    
    def persistent_node(name, func):
        """Wrapper to ensure every node saves a persistent checkpoint."""
        def wrapper(state: StudioState):
            print(f"--- [OS] Persistent Node: {name} ---")
            
            result = func(state)
            if not isinstance(result, dict):
                result = {}

            # Special logic for strategist: increment cycle_count in the return dict
            if name == "strategist":
                result["cycle_count"] = state.get("cycle_count", 0) + 1
            
            # Merge results for the checkpoint
            new_state = {**state, **result}
            
            # CRITICAL: Strip non-serializable objects before saving
            clean_state = {k: v for k, v in new_state.items() if k != "integrator"}
            StateStore.save_checkpoint(state["project_id"], name, clean_state)
            
            # Sync operational truth to DB
            from src.shared.db import ProjectOS, Session, engine, Project # type: ignore
            
            # Check if current status is already 'High Value' (e.g. Needs Review)
            with Session(engine) as session:
                project = session.get(Project, state["project_id"])
                current_status = project.status if project else ""
                
            if "Review" not in current_status and "Ready" not in current_status:
                ProjectOS.update_status(state["project_id"], name, f"Agent {name} Active", cycles=new_state.get("cycle_count", 0))
            else:
                # Just update pulse/health without overwriting status
                ProjectOS.update_status(state["project_id"], name, current_status, cycles=new_state.get("cycle_count", 0))
            
            return result
        return wrapper

    # 1. Operative Nodes
    workflow.add_node("growth", persistent_node("growth", growth_agent))
    workflow.add_node("cfo", persistent_node("cfo", cfo_agent))
    
    # 2. Creative Nodes
    workflow.add_node("researcher", persistent_node("researcher", researcher_agent))
    workflow.add_node("strategist", persistent_node("strategist", strategy_agent))
    workflow.add_node("critic", persistent_node("critic", intelligence_critic_agent))
    workflow.add_node("director", persistent_node("director", director_agent))
    workflow.add_node("stylist", persistent_node("stylist", visual_stylist_agent))
    workflow.add_node("ui_ux", persistent_node("ui_ux", ui_architect_agent))
    workflow.add_node("social", persistent_node("social", social_growth_agent))
    workflow.add_node("packaging", persistent_node("packaging", packaging_agent))
    workflow.add_node("motion", persistent_node("motion", motion_choreographer_agent))
    
    # 3. Edges & Logic
    workflow.set_entry_point("growth")
    workflow.add_edge("growth", "cfo")
    workflow.add_edge("cfo", "researcher")
    workflow.add_edge("researcher", "strategist")
    workflow.add_edge("strategist", "critic")
    
    # NEW: Critic Feedback Loop
    def route_critic(state: StudioState):
        if state.get("critic_feedback") == "CRITIC_PASSED" or state.get("cycle_count", 0) >= 3:
            return "passed"
        return "rejected"

    workflow.add_conditional_edges(
        "critic",
        route_critic,
        {
            "passed": "director",
            "rejected": "strategist"
        }
    )

    # All paths that pass audit lead to the Director for synthesis
    workflow.add_edge("director", "check_review_gate")

    # Review Gate Logic
    def check_review_status(state: StudioState):
        if state.get("methodology") == "VERIFICATION":
            return "approved"
        from src.shared.db import Project, Session, engine  # type: ignore
        with Session(engine) as session:
            project = session.get(Project, state["project_id"])
            if project and project.review_status == "APPROVED":
                return "approved"
            return "pending"

    # Pass-through node for clarity before the final gate
    workflow.add_node("check_review_gate", lambda x: x)
    
    workflow.add_conditional_edges(
        "check_review_gate",
        check_review_status,
        {
            "approved": "stylist",
            "pending": END
        }
    )

    workflow.add_edge("stylist", "ui_ux")
    workflow.add_edge("stylist", "social")
    workflow.add_edge("stylist", "packaging")
    workflow.add_edge("ui_ux", "motion")
    workflow.add_edge("social", "motion")
    workflow.add_edge("packaging", "motion")
    workflow.add_edge("motion", END)
    
    return workflow.compile()


def run_studio_pipeline(brief: str, budget: float = 1000.0, project_name: str = "Untitled Project", methodology: str = "STANDARD", clarifying_questions: List[str] = [], project_id: Optional[int] = None):
    """
    Run the full creative pipeline for a given brief.
    """
    from src.shared.db import create_db_and_tables, Project, Session, engine  # type: ignore
    from src.operative_core.integrator import IntegratorAgent, GeminiIntegration, DriveIntegration  # type: ignore
    
    # Init DB
    create_db_and_tables()
    
    # 1. Project Initialization & Resume Logic
    if project_id is None:
        with Session(engine) as session:
            project = Project(
                name=project_name, 
                client_brief=brief, 
                budget_cap=budget,
                status="Intake"
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            project_id = project.id # type: ignore
    else:
        # RESUME LOGIC (The Black Box)
        with Session(engine) as session:
            project = session.get(Project, project_id)
            if project:
                brief = project.client_brief
                project_name = project.name
                project.status = "Resuming"
                session.add(project)
                session.commit()
        
        cached_state = StateStore.load_checkpoint(project_id)
        if cached_state:
            print(f"--- [OS] Resuming Project {project_id} from Black Box ---")

    # 2. Financial Lock (CFO Gate)
    from src.shared.bank import StudioBank, COST_TABLE # type: ignore
    from src.shared.db import Project, Session, engine # type: ignore
    
    bank = StudioBank(budget)
    # Check for a minimum operating liquidity (e.g. 100 units)
    if not bank.check_funds(100.0):
        print("❌ FINANCIAL LOCK: Project paused due to insufficient symbolic funds.")
        with Session(engine) as session:
            project = session.get(Project, project_id)
            if project:
                project.is_locked = True
                project.status = "LOCKED: Insufficient Funds"
                session.add(project)
                session.commit()
        return {"error": "FINANCIAL_LOCK_ACTIVE"}
    else:
        # Ensure lock is cleared if funds are sufficient
        with Session(engine) as session:
            project = session.get(Project, project_id)
            if project and project.is_locked:
                project.is_locked = False
                session.add(project)
                session.commit()

    # Init Integrator
    integrator = IntegratorAgent(project_id) # type: ignore
    integrator.register_integration(GeminiIntegration("Gemini", {}))
    integrator.register_integration(DriveIntegration("Drive", {}))
    integrator.connect_all()

    # Build & run workflow
    app = _build_workflow()

    print(f"\n--- Templo Atelier (Project ID: {project_id}) ---")
    print(f"Project: {project_name}")
    print(f"Methodology: {methodology}")
    print(f"Brief: {brief[:100]}...")  # type: ignore
    
    # Prepare Initial State (or use cached)
    initial_state = {
        "client_brief": brief, 
        "project_budget_tokens": budget,
        "project_id": project_id,
        "project_name": project_name,
        "methodology": methodology,
        "integrator": integrator,
        "market_research": None,
        "critic_feedback": "CRITIC_PASSED",
        "cycle_count": 0,
        "executive_summary": None,
        "clarifying_questions": clarifying_questions,
        "is_complete": len(clarifying_questions) == 0
    }
    
    if project_id and StateStore.load_checkpoint(project_id):
         # Merge with cached state for real resume
         initial_state.update(StateStore.load_checkpoint(project_id)) # type: ignore

    result = app.invoke(initial_state)
    
    print("\n--- Studio Run Complete ---")
    return result


def run_studio():
    """Demo entrypoint with a sample brief."""
    initial_brief = "A futuristic coffee brand called 'Nebula Brew' targeting tech workers."
    result = run_studio_pipeline(initial_brief, budget=1000.0, project_name="Nebula Brew")
    print(result)


if __name__ == "__main__":
    run_studio()
