from fastapi import FastAPI, Depends, HTTPException # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
from sqlmodel import Session, select, func # type: ignore
from typing import List, Dict, Any
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from src.shared.db import Project, AgentLog, InterventionRequest, CalendarEvent, GlobalTask, Deliverable, Risk, Invoice, Document, AgentRequest, WorkflowStep, create_db_and_tables, get_session # type: ignore
from src.operative_core.studio import studio
from src.operative_core.agent_base import AgentInput
from src.dashboard_api.agent_intel import (
    generate_strategic_directions_llm,
    expand_strategy_llm,
    generate_research_doc_content,
    recommend_deliverables_llm
)

app = FastAPI(title="Templo Atelier API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local dev, allow all. In prod, restrict this.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- Categories (Information Architecture) ---

CATEGORY_ICONS = {
    "Brand Identity": "◆",
    "Web Design": "◎",
    "Packaging": "▣",
    "Product Design": "△",
}

def _slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("&", "and")

@app.get("/categories/")
def get_categories(session: Session = Depends(get_session)):
    """Returns all service categories with aggregated project data."""
    projects = session.exec(select(Project)).all()
    cat_map: Dict[str, list] = {}
    for p in projects:
        cat_map.setdefault(p.category, []).append(p)

    # Also include default categories even if empty
    for default_cat in CATEGORY_ICONS:
        cat_map.setdefault(default_cat, [])

    result = []
    for cat_name, cat_projects in sorted(cat_map.items()):
        status_breakdown: Dict[str, int] = {}
        needs_attention = False
        for p in cat_projects:
            stage = p.stage or "Intake"
            status_breakdown[stage] = status_breakdown.get(stage, 0) + 1
            # Attention: pending review, blockers, or stalled health
            if p.review_status == "PENDING" or p.blocker_summary or p.health_score < 70:
                needs_attention = True
        result.append({
            "name": cat_name,
            "slug": _slug(cat_name),
            "icon": CATEGORY_ICONS.get(cat_name, "●"),
            "project_count": len(cat_projects),
            "status_breakdown": status_breakdown,
            "needs_attention": needs_attention,
        })
    return result

@app.get("/categories/{slug}/projects")
def get_category_projects(slug: str, session: Session = Depends(get_session)):
    """Returns projects filtered by category slug."""
    projects = session.exec(select(Project)).all()
    filtered = [p for p in projects if _slug(p.category) == slug]
    if not filtered and slug not in [_slug(c) for c in CATEGORY_ICONS]:
        raise HTTPException(status_code=404, detail=f"Category '{slug}' not found")
    return filtered

# --- Projects ---

@app.get("/projects/", response_model=List[Project])
def read_projects(session: Session = Depends(get_session)):
    projects = session.exec(select(Project)).all()
    return projects

@app.post("/projects/", response_model=Project)
def create_project(project: Project, session: Session = Depends(get_session)):
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

# --- Logs (Live Feed) ---

@app.get("/logs/", response_model=List[AgentLog])
def read_logs(limit: int = 50, session: Session = Depends(get_session)):
    logs = session.exec(select(AgentLog).order_by(AgentLog.timestamp.desc()).limit(limit)).all()
    return logs

@app.post("/logs/", response_model=AgentLog)
def create_log(log: AgentLog, session: Session = Depends(get_session)):
    # Also update project budget if cost is incurred
    if log.cost_incurred > 0:
        project = session.get(Project, log.project_id)
        if project:
            project.budget_spent += log.cost_incurred
            session.add(project)
    
    session.add(log)
    session.commit()
    session.refresh(log)
    return log

# --- Interventions ---

@app.get("/interventions/", response_model=List[InterventionRequest])
def read_interventions(session: Session = Depends(get_session)):
    requests = session.exec(select(InterventionRequest).where(InterventionRequest.status == "PENDING")).all()
    return requests

@app.post("/interventions/{request_id}/approve")
def approve_intervention(request_id: int, session: Session = Depends(get_session)):
    req = session.get(InterventionRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "APPROVED"
    session.add(req)
    session.commit()
    return {"ok": True}

# --- System Health (Meta-Agent Audit) ---

@app.get("/system/audit/")
def get_system_audit():
    """Returns the latest Meta-Agent optimization report."""
    audit_dir = Path("storage/system/audit")
    if not audit_dir.exists():
        return {"report": "No audit reports found yet."}
    
    reports = sorted(list(audit_dir.glob("*.md")), reverse=True)
    if not reports:
        return {"report": "No audit reports found yet."}
    
    with open(reports[0], "r") as f:
        return {"report": f.read()}

@app.get("/calendar/", response_model=List[CalendarEvent])
def get_calendar(session: Session = Depends(get_session)):
    from sqlmodel import select # type: ignore
    return session.exec(select(CalendarEvent)).all()

@app.get("/tasks/", response_model=List[GlobalTask])
def get_tasks(session: Session = Depends(get_session)):
    from sqlmodel import select # type: ignore
    return session.exec(select(GlobalTask)).all()

@app.post("/tasks/")
def create_task(payload: dict, session: Session = Depends(get_session)):
    """Create a new task."""
    task = GlobalTask(
        title=payload.get("title", "Untitled Task"),
        priority=payload.get("priority", "Normal"),
        status=payload.get("status", "Todo"),
        project_id=payload.get("project_id"),
        due_date=datetime.utcnow(),
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@app.patch("/tasks/{task_id}")
def update_task(task_id: int, payload: dict, session: Session = Depends(get_session)):
    """Toggle task status or update fields."""
    task = session.get(GlobalTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if "status" in payload:
        task.status = payload["status"]
    if "title" in payload:
        task.title = payload["title"]
    if "priority" in payload:
        task.priority = payload["priority"]
    session.commit()
    session.refresh(task)
    return task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    """Delete a task."""
    task = session.get(GlobalTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return {"status": "deleted", "task_id": task_id}

# --- Document update endpoint ---
@app.patch("/documents/{doc_id}")
def update_document(doc_id: int, payload: dict, session: Session = Depends(get_session)):
    """Update document content."""
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if "content" in payload:
        doc.content = payload["content"]
        doc.version = (doc.version or 1) + 1
        doc.updated_at = datetime.utcnow()
    if "name" in payload:
        doc.name = payload["name"]
    session.commit()
    session.refresh(doc)
    return doc

# --- PDF / Strategy Export ---
@app.get("/founder/project/{project_id}/export")
def export_project_strategy(project_id: int, session: Session = Depends(get_session)):
    """Export project strategy as an HTML document suitable for saving as PDF."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    docs = session.exec(select(Document).where(Document.project_id == project_id)).all()
    tasks = session.exec(select(GlobalTask).where(GlobalTask.project_id == project_id)).all()
    risks_data = project.risks_json or "[]"
    strategy_data = project.strategy_json or "[]"
    
    try:
        risks = json.loads(risks_data)
    except:
        risks = []
    try:
        pillars = json.loads(strategy_data)
    except:
        pillars = []
    
    # Build HTML export
    doc_sections = ""
    for d in docs:
        doc_sections += f"<div class='doc-section'><h3>{d.name}</h3><p class='doc-cat'>{d.category}</p><div>{d.content or ''}</div></div>"
    
    task_rows = ""
    for t in tasks:
        status_icon = "✓" if t.status == "Done" else "○"
        task_rows += f"<tr><td>{status_icon}</td><td>{t.title}</td><td>{t.priority}</td></tr>"
    
    risk_items = ""
    for r in risks:
        text = r if isinstance(r, str) else r.get("item", str(r))
        risk_items += f"<li>{text}</li>"
    
    pillar_items = ""
    for p in pillars:
        pillar_items += f"<li>{p}</li>"
    
    from fastapi.responses import HTMLResponse
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{project.name} — Strategy Export</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif; max-width: 800px; margin: 40px auto; padding: 0 24px; color: #1d1d1f; line-height: 1.6; }}
  h1 {{ font-size: 2rem; font-weight: 700; letter-spacing: -0.02em; border-bottom: 2px solid #0071e3; padding-bottom: 8px; }}
  h2 {{ font-size: 1.25rem; color: #6e6e73; margin-top: 32px; }}
  h3 {{ font-size: 1rem; margin-top: 20px; }}
  .meta {{ color: #86868b; font-size: 0.875rem; margin-bottom: 32px; }}
  .doc-section {{ background: #f5f5f7; padding: 16px 20px; border-radius: 8px; margin: 12px 0; }}
  .doc-cat {{ font-size: 0.75rem; color: #86868b; margin: 2px 0 8px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
  th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid rgba(0,0,0,0.08); font-size: 0.875rem; }}
  th {{ font-weight: 600; color: #6e6e73; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  ul {{ padding-left: 20px; }}
  li {{ margin: 4px 0; }}
  .footer {{ margin-top: 48px; padding-top: 16px; border-top: 1px solid rgba(0,0,0,0.08); font-size: 0.75rem; color: #aeaeb2; }}
  @media print {{ body {{ margin: 0; }} }}
</style></head><body>
<h1>{project.name}</h1>
<div class="meta">
  <strong>Client:</strong> {project.client or 'N/A'} &nbsp;|&nbsp;
  <strong>Category:</strong> {project.category or 'N/A'} &nbsp;|&nbsp;
  <strong>Stage:</strong> {project.stage or 'N/A'} &nbsp;|&nbsp;
  <strong>Budget:</strong> ${'{:,.0f}'.format(project.budget_cap or 0)}
</div>

<h2>Executive Summary</h2>
<p>{project.executive_summary or 'Awaiting strategy generation…'}</p>

{'<h2>Strategic Pillars</h2><ul>' + pillar_items + '</ul>' if pillar_items else ''}
{'<h2>Active Risks</h2><ul>' + risk_items + '</ul>' if risk_items else ''}

<h2>Documents</h2>
{doc_sections if doc_sections else '<p style="color:#86868b">No documents generated yet.</p>'}

<h2>Task List</h2>
{'<table><tr><th></th><th>Task</th><th>Priority</th></tr>' + task_rows + '</table>' if task_rows else '<p style="color:#86868b">No tasks assigned yet.</p>'}

<div class="footer">
  Exported from Templo Atelier Studio OS &mdash; {datetime.utcnow().strftime('%B %d, %Y')}
</div>
</body></html>"""
    return HTMLResponse(content=html)

# --- FOUNDER OS API (v14.0) ---

@app.get("/founder/global")
def founder_global_pulse(session: Session = Depends(get_session)):
    """Top-level command center metrics."""
    projects = session.exec(select(Project)).all()
    active_projects = [p for p in projects if not p.is_lead]
    pipeline_projects = [p for p in projects if p.is_lead]
    
    total_active = len(active_projects)
    pipeline_vol = sum(p.projected_revenue for p in pipeline_projects)
    
    # Financials
    total_revenue_forecast = sum(p.projected_revenue for p in active_projects)
    total_invoiced = sum(p.invoiced_total for p in active_projects)
    total_cost = sum(p.internal_cost for p in active_projects)
    avg_margin = ((total_invoiced - total_cost) / total_invoiced * 100) if total_invoiced > 0 else 0.0
    
    # Risks
    critical_risks = session.exec(select(Risk).where(Risk.severity == "High", Risk.status == "Active")).all()
    
    return {
        "active_count": total_active,
        "pipeline_volume": pipeline_vol,
        "avg_margin": int(avg_margin * 10) / 10,
        "revenue_forecast": total_revenue_forecast,
        "critical_risks_count": len(critical_risks),
        "cashflow_status": "Healthy" if avg_margin > 30 else "Attention"
    }

@app.get("/founder/operations")
def founder_operations(session: Session = Depends(get_session)):
    """Operational density: Deliverables, Tasks, Deadlines."""
    now = datetime.utcnow()
    next_week = now + timedelta(days=7)
    
    # Deliverables due soon
    due_soon = session.exec(select(Deliverable).where(Deliverable.due_date >= now, Deliverable.due_date <= next_week)).all()
    overdue_delivs = session.exec(select(Deliverable).where(Deliverable.due_date < now, Deliverable.status != "Approved")).all()
    
    # Active Projects Health
    projects = session.exec(select(Project).where(Project.is_lead == False)).all()
    
    return {
        "deliverables_due_7d": len(due_soon),
        "deliverables_overdue": len(overdue_delivs),
        "active_projects": [{
            "id": p.id,
            "name": p.name,
            "stage": p.stage,
            "health": p.health_score,
            "next_milestone": p.next_milestone,
            "blocker": p.blocker_summary
        } for p in projects]
    }

@app.get("/founder/financials")
def founder_financials(session: Session = Depends(get_session)):
    """Deep financial integrity check."""
    invoices = session.exec(select(Invoice)).all()
    overdue = [i for i in invoices if i.status == "Overdue"]
    
    projects = session.exec(select(Project).where(Project.is_lead == False)).all()
    
    return {
        "overdue_invoices_count": len(overdue),
        "overdue_value": sum(i.amount for i in overdue),
        "project_financials": [{
            "name": p.name,
            "budget": p.budget_cap,
            "invoiced": p.invoiced_total,
            "cost": p.internal_cost,
            "margin": round(((p.invoiced_total - p.internal_cost) / p.invoiced_total * 100), 1) if p.invoiced_total > 0 else 0.0
        } for p in projects]
    }

@app.get("/founder/pipeline")
def founder_pipeline(session: Session = Depends(get_session)):
    """Revenue pipeline view."""
    leads = session.exec(select(Project).where(Project.is_lead == True)).all()
    return [{
        "id": p.id,
        "name": p.name,
        "value": p.projected_revenue,
        "status": p.status,
        "probability": 70 if p.stage == "Lead" else 30 # Mock logic
    } for p in leads]

@app.get("/founder/project/{project_id}")
def founder_project_deep(project_id: int, session: Session = Depends(get_session)):
    """v15.0: The God Endpoint for Project Command Center."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    deliverables = session.exec(select(Deliverable).where(Deliverable.project_id == project_id)).all()
    risks = session.exec(select(Risk).where(Risk.project_id == project_id)).all()
    invoices = session.exec(select(Invoice).where(Invoice.project_id == project_id)).all()
    tasks = session.exec(select(GlobalTask).where(GlobalTask.project_id == project_id)).all()
    documents = session.exec(select(Document).where(Document.project_id == project_id)).all() # NEW
    requests = session.exec(select(AgentRequest).where(AgentRequest.project_id == project_id)).all() # NEW
    
    # Computed Financials
    total_budget = project.budget_cap
    burn = project.internal_cost
    margin_val = project.invoiced_total - burn
    margin_percent = (margin_val / project.invoiced_total * 100) if project.invoiced_total > 0 else 0.0
    
    # 10-Part Modular Response
    return {
        "overview": {
            "id": project.id,
            "name": project.name,
            "client": "Standard Client", # Placeholder or add to model
            "type": "Branding", # Placeholder
            "stage": project.stage,
            "status": project.status,
            "pulse": "On Track", # Computed logic can go here
            "next_action": "Approve Strategy", # Computed from tasks/approvals
            "milestone": project.next_milestone,
            "deadline": project.deadline,
            "scope_stability": project.scope_stability,
            "margin_trend": project.margin_trend
        },
        "financials": {
            "budget": total_budget,
            "burn": burn,
            "margin_percent": round(margin_percent, 1), # type: ignore
            "invoiced": project.invoiced_total,
            "projected": project.projected_revenue
        },
        "strategy": {
            "brief": project.client_brief,
            "executive_summary": project.executive_summary,
            "strategy_json": project.strategy_json,
            "research_json": project.research_insights_json,
            "tensions": project.strategic_tensions,
            "principles": project.design_principles
        },
        "production": {
            "deliverables": deliverables,
            "tasks": tasks
        },
        "governance": {
            "risks": risks,
            "invoices": invoices,
            "approvals": [] # To be implemented in Part 9
        },
        "documents": documents, # v15.0
        "requests": requests,   # v15.0
        "creative_mode": {
            "objective": project.client_brief,
            "principles": project.design_principles,
            "tensions": project.strategic_tensions,
            "insights": project.research_insights_json
        }
    }

# --- New Project Onboarding (v16.0) ---

from pydantic import BaseModel # type: ignore
from typing import Optional

class NewProjectPayload(BaseModel):
    name: str
    category: Optional[str] = "Brand Identity"
    client: Optional[str] = None
    client_brief: Optional[str] = None
    budget_cap: Optional[float] = 0
    stage: Optional[str] = "Strategy"
    # Strategy
    executive_summary: Optional[str] = None
    strategic_tensions: Optional[str] = None
    design_principles: Optional[str] = None
    research_insights: Optional[str] = None
    # Deliverables
    deliverables: Optional[list] = []
    # Tasks
    tasks: Optional[list] = []

@app.post("/founder/project")
def create_project(payload: NewProjectPayload, session: Session = Depends(get_session)):
    """Create a new project from the onboarding wizard."""
    project = Project(
        name=payload.name,
        category=payload.category or "Brand Identity",
        client=payload.client or "",
        client_brief=payload.client_brief or "",
        budget_cap=payload.budget_cap or 0,
        status=payload.stage or "Strategy",
        stage=payload.stage or "Strategy",
        is_lead=False,
        health_score=100,
        projected_revenue=0,
        invoiced_total=0,
        internal_cost=0,
        internal_margin=0,
        executive_summary=payload.executive_summary or "",
        strategic_tensions=payload.strategic_tensions or "[]",
        design_principles=payload.design_principles or "[]",
        research_insights_json=payload.research_insights or "{}",
    )

    session.add(project)
    session.commit()
    session.refresh(project)

    # Add deliverables
    for d in (payload.deliverables or []):
        if isinstance(d, dict) and d.get('title'):
            session.add(Deliverable(
                project_id=project.id,
                title=d['title'],
                status=d.get('status', 'Pending'),
                owner=d.get('owner', 'Unassigned')
            ))

    # Add tasks
    for t in (payload.tasks or []):
        if isinstance(t, dict) and t.get('title'):
            session.add(GlobalTask(
                project_id=project.id,
                title=t['title'],
                priority=t.get('priority', 'Normal'),
                status='Todo'
            ))

    session.commit()
    return {"status": "created", "project_id": project.id, "name": project.name}

# --- AI Strategy Runner ---

@app.post("/founder/project/{project_id}/run-strategy")
def run_strategy(project_id: int, session: Session = Depends(get_session)):
    """Triggers AI strategy generation for a project using Gemini."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    brief = project.client_brief or project.executive_summary or project.name

    # 1. Generate strategic directions
    directions = generate_strategic_directions_llm(project.name, brief)

    # 2. Generate initial research documents (Context for Decision)
    for doc_type in ["market_landscape", "competitor_analysis"]:
        content = generate_research_doc_content(doc_type, project.name, brief, "Exploratory Phase")
        session.add(Document(
            project_id=project_id,
            name=doc_type.replace("_", " ").title(),
            category="Research",
            doc_type="html",
            content=content,
        ))
    
    # 3. Create Decision Gate Workflow Step
    step = WorkflowStep(
        project_id=project_id,
        step_type="decision_gate",
        agent="Strategist",
        title="Strategic Direction",
        body=f"Based on the brief — \"{brief}\" — I've analyzed the market positioning and competitive landscape. Here are 3 distinct strategic directions. Review the initial research documents in the 'Documents' tab, then choose the direction that best aligns with your vision.",
        options_json=json.dumps(directions),
        status="active",
        phase="strategy",
        sort_order=1
    )
    session.add(step)

    # Update project status to notify user
    project.review_status = "PENDING"
    session.add(project)

    # 4. Add Phase 1 Tasks
    phase1_tasks = ["Phase 1: Review Market Analysis", "Phase 1: Select Strategic Direction"]
    for task_title in phase1_tasks:
        session.add(GlobalTask(
            project_id=project_id,
            title=task_title,
            priority="High",
            status="Todo",
            due_date=datetime.utcnow() + timedelta(days=2)
        ))

    # 5. Log Event
    session.add(AgentLog(
        project_id=project_id,
        agent_name="Strategist",
        message=f"Strategic analysis complete. {len(directions)} directions proposed for review.",
    ))

    session.commit()
    session.refresh(project)
    return {"status": "ok", "directions": directions, "next_step": "decision_gate"}


@app.delete("/founder/project/{project_id}")
def delete_project(project_id: int, session: Session = Depends(get_session)):
    """Delete a project and all associated data."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete all associated records
    for model in [WorkflowStep, Deliverable, GlobalTask, Document, Risk, Invoice, AgentRequest, AgentLog]:
        items = session.exec(select(model).where(model.project_id == project_id)).all()  # type: ignore
        for item in items:
            session.delete(item)

    session.delete(project)
    session.commit()
    return {"status": "deleted", "project_id": project_id}

# --- Patch Project (v17.0 — inline updates) ---

class ProjectPatch(BaseModel):
    executive_summary: Optional[str] = None
    strategic_tensions: Optional[str] = None
    design_principles: Optional[str] = None
    client_brief: Optional[str] = None
    budget_cap: Optional[float] = None
    stage: Optional[str] = None

@app.patch("/founder/project/{project_id}")
def patch_project(project_id: int, patch: ProjectPatch, session: Session = Depends(get_session)):
    """Update specific fields of a project (inline editing)."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for key, value in patch.dict(exclude_unset=True).items():
        if value is not None:
            setattr(project, key, value)

    session.add(project)
    session.commit()
    session.refresh(project)
    return {"status": "updated", "project_id": project.id}

# --- Workflow Engine (v17.0) ---

@app.get("/founder/project/{project_id}/workflow")
def get_workflow(project_id: int, session: Session = Depends(get_session)):
    """Get all workflow steps for a project, ordered chronologically."""
    steps = session.exec(
        select(WorkflowStep)
        .where(WorkflowStep.project_id == project_id)
        .order_by(WorkflowStep.sort_order)  # type: ignore
    ).all()
    result = []
    for s in steps:
        result.append({
            "id": s.id,
            "step_type": s.step_type,
            "agent": s.agent,
            "title": s.title,
            "body": s.body,
            "options": json.loads(s.options_json) if s.options_json else [],
            "chosen_option": s.chosen_option,
            "status": s.status,
            "phase": s.phase,
            "sort_order": s.sort_order,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "resolved_at": s.resolved_at.isoformat() if s.resolved_at else None,
        })
    return result

class WorkflowResolvePayload(BaseModel):
    step_id: int
    action: str          # choose | approve | reject | input
    chosen_option: Optional[str] = None
    input_text: Optional[str] = None

@app.post("/founder/project/{project_id}/workflow/resolve")
def resolve_workflow_step(project_id: int, payload: WorkflowResolvePayload, session: Session = Depends(get_session)):
    """Founder resolves a workflow step — picks an option, approves, or provides input."""
    step = session.get(WorkflowStep, payload.step_id)
    if not step or step.project_id != project_id:
        raise HTTPException(status_code=404, detail="Step not found")

    step.status = "resolved"
    step.resolved_at = datetime.utcnow()
    step.chosen_option = payload.chosen_option or payload.input_text or payload.action

    session.add(step)
    session.commit()

    # --- CHAIN REACTION: Generate next steps based on what was resolved ---
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404)

    next_steps = generate_next_steps(step, project, payload, session)

    session.commit()
    return {"status": "resolved", "step_id": step.id, "next_steps_created": len(next_steps)}

def generate_next_steps(resolved_step: WorkflowStep, project: Project, payload: WorkflowResolvePayload, session: Session) -> list:
    """Template-based agent chain — generates next workflow steps based on what was just resolved."""
    created = []
    max_order = resolved_step.sort_order

    if resolved_step.step_type == "input_needed" and resolved_step.title == "Project Brief":
        # Founder submitted their brief → Update project, then Strategist generates 3 directions
        if payload.input_text:
            project.client_brief = payload.input_text
            session.add(project)

        brief = payload.input_text or project.client_brief or project.name
        
        # vFinal Integration: Use Guilds (Strategist)
        try:
            inp = AgentInput(
                task_description="generate_directions",
                context_data={"project_name": project.name, "brief": brief}
            )
            out = studio.agents["strategist"].run(inp)
            directions = out.structured_data.get("directions", [])
            if not directions:
                 # Fallback if structure missing (simplistic error handling)
                 directions = [{"key": "A", "title": "Strategy Error", "description": "Could not generate strategy."}]
        except Exception as e:
             # Log error via Observability?
             directions = [{"key": "A", "title": "System Error", "description": f"Strategist failed: {e}"}]

        step = WorkflowStep(
            project_id=project.id,
            step_type="decision_gate",
            agent="Strategist",
            title="Strategic Direction",
            body=f"Based on the brief — \"{brief}\" — I've analyzed the market positioning, audience signals, and competitive landscape for **{project.name}**. Here are 3 distinct strategic directions, each leading to a different brand architecture and visual language. Choose the one that resonates most with your vision.",
            options_json=json.dumps(directions),
            status="active",
            phase="strategy",
            sort_order=max_order + 1
        )
        session.add(step)
        created.append(step)

        # --- GENERATE DOCUMENTS: Market Landscape + Competitor Analysis ---
        session.add(Document(
            project_id=project.id,
            name="Market Landscape Analysis",
            category="Strategy",
            doc_type="html",
            content=generate_research_doc_content("market_landscape", project.name, brief)
        ))
        session.add(Document(
            project_id=project.id,
            name="Competitive Analysis",
            category="Strategy",
            doc_type="html",
            content=generate_research_doc_content("competitor_analysis", project.name, brief)
        ))

    elif resolved_step.step_type == "decision_gate" and resolved_step.title == "Strategic Direction":
        # Founder picked a direction → Strategist expands it into full strategy
        chosen = payload.chosen_option or "A"
        options = json.loads(resolved_step.options_json)
        chosen_dir = next((o for o in options if o["key"] == chosen), options[0])
        
        brief = project.client_brief or project.name
        
        # vFinal Integration: Strategist Expands
        try:
             inp = AgentInput(
                 task_description="expand_strategy", 
                 context_data={"project_name": project.name, "brief": brief, "direction": chosen_dir}
             )
             out = studio.agents["strategist"].run(inp)
             strategy = out.structured_data.get("strategy", {})
             if not strategy:
                # Fallback
                 strategy = {"positioning": "Error", "pillars": ["Error"], "tensions": [], "principles": []}
        except Exception as e:
             strategy = {"positioning": f"Error: {e}", "pillars": [], "tensions": [], "principles": []}
             
        strategy_summary = f"{strategy.get('positioning', '')} | Pillars: {', '.join(strategy.get('pillars', []))}"

        strategy_body = f"""## {chosen_dir['title']} — Expanded Strategy for {project.name}

**Positioning**: {strategy['positioning']}

**Brand Pillars**:
{chr(10).join(f'- {p}' for p in strategy['pillars'])}

**Strategic Tensions**:
{chr(10).join(f'- {t}' for t in strategy['tensions'])}

**Design Principles**:
{chr(10).join(f'- {p}' for p in strategy['principles'])}"""

        # Update project with strategy
        project.executive_summary = f"{chosen_dir['title']}: {chosen_dir['description']}"
        project.strategic_tensions = json.dumps(strategy["tensions"])
        project.design_principles = json.dumps(strategy["principles"])
        session.add(project)

        # --- GENERATE DOCUMENTS: Brand Positioning + Target Audience ---
        session.add(Document(
            project_id=project.id,
            name="Brand Positioning Report",
            category="Strategy",
            doc_type="html",
            content=generate_research_doc_content("brand_positioning", project.name, brief, strategy_summary)
        ))
        session.add(Document(
            project_id=project.id,
            name="Target Audience Profile",
            category="Strategy",
            doc_type="html",
            content=generate_research_doc_content("target_audience", project.name, brief, strategy_summary)
        ))

        step = WorkflowStep(
            project_id=project.id,
            step_type="approval_gate",
            agent="Strategist",
            title="Strategy Review",
            body=strategy_body,
            options_json=json.dumps([{"key": "approve", "title": "Approve & proceed to planning"}, {"key": "revise", "title": "Request revisions"}]),
            status="active",
            phase="strategy",
            sort_order=max_order + 1
        )
        session.add(step)
        created.append(step)

        # --- Add Phase 2 Tasks ---
        phase2_tasks = ["Phase 2: Review Full Strategy", "Phase 2: Approve Brand Pillars"]
        for task_title in phase2_tasks:
            session.add(GlobalTask(
                project_id=project.id,
                title=task_title,
                priority="High",
                status="Todo",
                due_date=datetime.utcnow() + timedelta(days=3)
            ))

        # --- Add Phase 2 Tasks ---
        phase2_tasks = ["Phase 2: Review Full Strategy", "Phase 2: Approve Brand Pillars"]
        for task_title in phase2_tasks:
            session.add(GlobalTask(
                project_id=project.id,
                title=task_title,
                priority="High",
                status="Todo",
                due_date=datetime.utcnow() + timedelta(days=3)
            ))



    elif resolved_step.step_type == "approval_gate" and resolved_step.title == "Strategy Review":
        action = payload.action
        if action == "approve" or payload.chosen_option == "approve":
            # Strategy approved → milestone + Director proposes deliverables
            milestone = WorkflowStep(
                project_id=project.id,
                step_type="milestone",
                agent="System",
                title="Strategy Phase Complete",
                body="✓ Strategic direction approved. Moving to production planning.",
                status="resolved",
                phase="strategy",
                sort_order=max_order + 1,
                resolved_at=datetime.utcnow()
            )
            session.add(milestone)
            created.append(milestone)

            # --- GENERATE DOCUMENTS: Brand Strategy Doc + Visual Direction Brief ---
            session.add(Document(
                project_id=project.id,
                name="Brand Strategy Document",
                category="Strategy",
                doc_type="html",
                content=generate_research_doc_content("brand_strategy_doc", project.name, project.client_brief or '', project.executive_summary or '')
            ))
            session.add(Document(
                project_id=project.id,
                name="Visual Direction Brief",
                category="Design",
                doc_type="html",
                content=generate_research_doc_content("visual_direction_brief", project.name, project.client_brief or '', project.executive_summary or '')
            ))

            # --- Director proposes BUDGET-AWARE deliverables ---
            budget: int = int(project.budget_cap or 0)

            # Deliverable catalog with estimated costs, time, and justification (AUDIT TRAIL)
            catalog: list[dict[str, object]] = [
                {"key": "brand_strategy", "title": "Brand Strategy Document", "cost": 800, "phase": "Foundation", "time_est": "1 week", "justification": "Defines core DNA and market positioning."},
                {"key": "visual_brief", "title": "Visual Identity Brief", "cost": 600, "phase": "Foundation", "time_est": "3 days", "justification": "Translates strategy into visual direction for designers."},
                {"key": "competitor_audit", "title": "Competitor Audit Report", "cost": 500, "phase": "Foundation", "time_est": "4 days", "justification": "Identifies whitespace opportunities in the market."},
                {"key": "logo_system", "title": "Logo & Identity System", "cost": 1500, "phase": "Design", "time_est": "2 weeks", "justification": "Core asset for brand recognition across all touchpoints."},
                {"key": "brand_guidelines", "title": "Brand Guidelines", "cost": 1000, "phase": "Design", "time_est": "1 week", "justification": "Ensures consistency in future brand application."},
                {"key": "visual_templates", "title": "Key Visual Templates", "cost": 700, "phase": "Design", "time_est": "1 week", "justification": "Ready-to-use assets for social and presentations."},
                {"key": "website", "title": "Website Design & Development", "cost": 2500, "phase": "Production", "time_est": "3 weeks", "justification": "Primary digital storefront and conversion engine."},
                {"key": "social_kit", "title": "Social Media Kit", "cost": 800, "phase": "Production", "time_est": "1 week", "justification": "Launch content to build initial traction."},
                {"key": "launch_collateral", "title": "Launch Collateral", "cost": 600, "phase": "Production", "time_est": "1 week", "justification": "Physical/digital assets for launch event/campaign."},
            ]

            # Auto-select deliverables that fit the budget (using Director Agent)
            # vFinal Integration: Director Recommends
            recommended_keys = []
            try:
                inp = AgentInput(
                    task_description="recommend_deliverables",
                    context_data={"project_name": project.name, "brief": project.client_brief or ""},
                    parameters={"budget": budget, "catalog": catalog}
                )
                out = studio.agents["director"].run(inp)
                recommended_keys = out.structured_data.get("selected_keys", [])
            except Exception:
                recommended_keys = []
            
            selected: list[str] = []
            running_total: int = 0
            for item in catalog:
                cost = int(item.get("cost", 0))  # type: ignore[arg-type]
                # If LLM recommended it, try to select it. Or if budget allows and we are in fallback mode.
                is_recommended = str(item.get("key")) in recommended_keys
                
                # Logic: If recommended and fits budget, select it.
                # If budget is 0, select everything recommended? Or just let user decide.
                # We stick to the rule: must fit budget if budget > 0.
                
                if budget <= 0 or (is_recommended and running_total + cost <= budget):
                    item["selected"] = True
                    selected.append(str(item["title"]))
                    running_total += cost
                else:
                    item["selected"] = False

            total_estimated: int = running_total
            remaining: int = budget - total_estimated if budget > 0 else 0

            if budget > 0:
                budget_line = f"**Budget:** ${budget:,.0f} · **Estimated scope cost:** ${total_estimated:,.0f} · **Remaining:** ${remaining:,.0f}"
                if remaining < 0:
                    budget_note = "\n\n⚠️ I've pre-selected deliverables that fit within your budget. You can adjust the selection below."
                elif remaining > 500:
                    budget_note = f"\n\n✅ Budget has room. You could add custom deliverables or increase scope."
                else:
                    budget_note = "\n\n✅ Scope fits your budget. Review and adjust as needed."
            else:
                budget_line = "**Budget:** Not set — showing full recommended scope."
                budget_note = "\n\n⚠️ No budget set. All deliverables are included. Set a budget in project settings to enable cost tracking."

            # Generate Audit Table
            audit_table = "| Item | Cost | Time | Rationale |\n| :--- | :--- | :--- | :--- |\n"
            for item in catalog:
                if item.get("selected"):
                    title = str(item.get("title", ""))
                    cost = str(item.get("cost", 0))
                    time = str(item.get("time_est", "-"))
                    justif = str(item.get("justification", ""))
                    audit_table += f"| **{title}** | ${cost} | {time} | {justif} |\n"

            deliverables_body = f"""Based on the approved strategy and a budget analysis, here is the justified scope breakdown:

{budget_line}

### Recommended Scope Audit
{audit_table}

{budget_note}

Review the full selection below to approve or adjust."""

            step = WorkflowStep(
                project_id=project.id,
                step_type="decision_gate",
                agent="Director",
                title="Deliverable Selection",
                body=deliverables_body,
                options_json=json.dumps(catalog),
                status="active",
                phase="design",
                sort_order=max_order + 2
            )
            session.add(step)
            created.append(step)

            # Update status for approval
            if payload.chosen_option == "revise":
                project.review_status = "REJECTED"
            else:
                project.review_status = "PENDING"
            session.add(project)

        else:
            # Rejected/Revise → ask for revisions
            step = WorkflowStep(
                project_id=project.id,
                step_type="input_needed",
                agent="Strategist",
                title="Strategy Revisions",
                body="What would you like me to change about the strategic direction? Please describe what feels off or what you'd like to emphasize differently.",
                status="active",
                phase="strategy",
                sort_order=max_order + 1
            )
            session.add(step)
            created.append(step)
            
            project.review_status = "REJECTED"
            session.add(project)

    elif resolved_step.step_type == "decision_gate" and resolved_step.title == "Deliverable Selection":
        # Founder confirmed deliverables → create them + budget summary
        project.review_status = "APPROVED"
        session.add(project)

        chosen = payload.chosen_option or ""
        custom_input = payload.input_text or ""

        # Parse chosen deliverables (comma-separated keys or JSON array)
        chosen_keys: list[str] = []
        try:
            parsed = json.loads(chosen) if chosen.startswith('[') else None
            if isinstance(parsed, list):
                chosen_keys = [str(k) for k in parsed]
            else:
                chosen_keys = [k.strip() for k in chosen.split(',') if k.strip()]
        except Exception:
            chosen_keys = [k.strip() for k in chosen.split(',') if k.strip()]

        catalog: list[dict[str, object]] = json.loads(resolved_step.options_json)
        total_cost: int = 0
        created_titles: list[str] = []

        for item in catalog:
            if str(item.get("key", "")) in chosen_keys:
                session.add(Deliverable(
                    project_id=project.id,
                    title=str(item["title"]),
                    status="Pending",
                    owner="Agent"
                ))
                item_cost = int(item.get("cost", 0))  # type: ignore[arg-type]
                total_cost += item_cost
                created_titles.append(f"{item['title']} (${item_cost:,})")

        # Add custom deliverables from manual input
        if custom_input:
            for custom in [c.strip() for c in custom_input.split(',') if c.strip()]:
                session.add(Deliverable(
                    project_id=project.id,
                    title=custom,
                    status="Pending",
                    owner="Founder"
                ))
                created_titles.append(f"{custom} (custom)")

        # Update project stage
        project.stage = "Design"
        project.status = "Design"
        session.add(project)

        # CFO confirms the final budget allocation
        budget = project.budget_cap or 0
        remaining = budget - total_cost if budget > 0 else 0
        margin_pct = ((budget - total_cost) / budget * 100) if budget > 0 else 0

        titles_formatted = '\n'.join(f'- {t}' for t in created_titles)
        budget_body = f"""**Deliverables Confirmed** — {len(created_titles)} items locked in.

{titles_formatted}

---

**Total estimated cost:** ${total_cost:,.0f}
**Project budget:** {f'${budget:,.0f}' if budget > 0 else 'Not set'}
**Remaining budget:** {f'${remaining:,.0f}' if budget > 0 else 'N/A'}
**Projected margin:** {f'{margin_pct:.0f}%' if budget > 0 else 'N/A'}

{'✅ Budget allocation approved. Design phase begins.' if remaining >= 0 else '⚠️ Scope exceeds budget by $' + f'{abs(remaining):,.0f}' + '. Consider adjusting scope or increasing budget.'}"""

        milestone = WorkflowStep(
            project_id=project.id,
            step_type="milestone",
            agent="System",
            title="Deliverables Confirmed",
            body=f"✓ {len(created_titles)} deliverables created. Moving to Design phase.",
            status="resolved",
            phase="design",
            sort_order=max_order + 1,
            resolved_at=datetime.utcnow()
        )
        session.add(milestone)
        created.append(milestone)

        step = WorkflowStep(
            project_id=project.id,
            step_type="agent_output",
            agent="CFO",
            title="Budget Allocation",
            body=budget_body,
            status="active",
            phase="design",
            sort_order=max_order + 2
        )
        session.add(step)
        created.append(step)

    return created

@app.post("/founder/project/{project_id}/workflow/seed")
def seed_workflow(project_id: int, session: Session = Depends(get_session)):
    """Seed the initial workflow for a project (first step: provide brief)."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if workflow already exists
    existing = session.exec(
        select(WorkflowStep).where(WorkflowStep.project_id == project_id)
    ).first()
    if existing:
        return {"status": "exists", "message": "Workflow already initialized"}

    # Create first step
    step = WorkflowStep(
        project_id=project_id,
        step_type="input_needed",
        agent="Strategist",
        title="Project Brief",
        body=f"Welcome to {project.name}. Before I can begin strategic analysis, I need to understand what we're building.\n\nDescribe the project in your own words — the vision, the audience, what makes it different. Don't worry about being polished; raw intent is more useful than corporate language.",
        status="active",
        phase="strategy",
        sort_order=0
    )
    session.add(step)
    session.commit()
    return {"status": "seeded", "step_id": step.id}

# --- Document Viewer API ---

@app.get("/founder/project/{project_id}/document/{doc_id}")
def get_document(project_id: int, doc_id: int, session: Session = Depends(get_session)):
    """Get a single document with full HTML content."""
    doc = session.get(Document, doc_id)
    if not doc or doc.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id,
        "name": doc.name,
        "category": doc.category,
        "doc_type": doc.doc_type,
        "content": doc.content,
        "version": doc.version,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
    }

# --- Document HTML Template Generators ---

def _doc_shell(title: str, agent: str, body: str) -> str:
    """Wraps body content in a consistent, professional HTML shell."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Inter', -apple-system, sans-serif; background:#0d0d0f; color:#e0ddd5; line-height:1.7; padding:48px 64px; max-width:920px; margin:0 auto; }}
  h1 {{ font-size:2rem; font-weight:700; color:#c8a96e; margin-bottom:8px; }}
  h2 {{ font-size:1.3rem; font-weight:600; color:#e0ddd5; margin:32px 0 12px; border-bottom:1px solid rgba(200,169,110,0.2); padding-bottom:8px; }}
  h3 {{ font-size:1rem; font-weight:600; color:#c8a96e; margin:20px 0 8px; }}
  p {{ margin:0 0 14px; font-size:0.92rem; color:#a09b8c; }}
  .meta {{ font-size:0.75rem; color:#706b5e; margin-bottom:32px; }}
  .meta span {{ color:#c8a96e; }}
  ul, ol {{ padding-left:20px; margin:8px 0 16px; }}
  li {{ font-size:0.9rem; color:#a09b8c; margin-bottom:6px; }}
  table {{ width:100%; border-collapse:collapse; margin:16px 0 24px; }}
  th {{ text-align:left; padding:10px 14px; background:rgba(200,169,110,0.08); border:1px solid rgba(200,169,110,0.15); color:#c8a96e; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.04em; }}
  td {{ padding:10px 14px; border:1px solid rgba(255,255,255,0.06); font-size:0.85rem; color:#a09b8c; }}
  .highlight {{ background:rgba(200,169,110,0.06); border-left:3px solid #c8a96e; padding:16px 20px; border-radius:6px; margin:16px 0; }}
  .highlight p {{ margin:0; color:#e0ddd5; }}
  .tag {{ display:inline-block; padding:3px 10px; background:rgba(200,169,110,0.1); border-radius:4px; font-size:0.72rem; color:#c8a96e; font-weight:600; margin-right:6px; }}
  .section-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin:16px 0; }}
  .card {{ background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:16px; }}
  .card h3 {{ margin-top:0; }}
  .score {{ font-size:2rem; font-weight:700; color:#c8a96e; }}
  .bar {{ height:6px; background:rgba(200,169,110,0.15); border-radius:3px; margin:8px 0; }}
  .bar-fill {{ height:100%; background:#c8a96e; border-radius:3px; }}
  hr {{ border:none; border-top:1px solid rgba(255,255,255,0.06); margin:32px 0; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="meta">Generated by <span>@{agent}</span> · Templo Atelier</div>
{body}
</body>
</html>"""

def generate_market_landscape_html(name: str, brief: str) -> str:
    return _doc_shell(f"Market Landscape — {name}", "Strategist", f"""
<div class="highlight"><p><strong>Brief:</strong> {brief}</p></div>

<h2>Industry Overview</h2>
<p>{name} operates in a space where cultural relevance, experiential value, and community identity intersect. The market is evolving rapidly as consumers shift from product-centric to experience-centric consumption models.</p>

<h3>Key Market Trends</h3>
<ul>
  <li><strong>Experience Economy:</strong> 78% of millennials prefer spending on experiences over products. The global experience economy is projected to reach $12.3B by 2027.</li>
  <li><strong>Conscious Consumption:</strong> Growing demand for brands that align with personal values — sustainability, authenticity, cultural depth.</li>
  <li><strong>Community-as-Product:</strong> Membership models and community platforms are replacing traditional brand-consumer relationships.</li>
  <li><strong>Hybrid Physical-Digital:</strong> Post-pandemic acceleration of phygital experiences, blending IRL with digital layers.</li>
  <li><strong>Curation over Volume:</strong> Market fatigue with algorithmically-driven content; growing appetite for human-curated, intentional offerings.</li>
</ul>

<h2>Market Size & Opportunity</h2>
<table>
  <tr><th>Segment</th><th>Size (2025)</th><th>Growth Rate</th><th>Relevance</th></tr>
  <tr><td>Experience Economy</td><td>$8.2B</td><td>+14% YoY</td><td><span class="tag">HIGH</span></td></tr>
  <tr><td>Cultural Events & Nightlife</td><td>$3.1B</td><td>+8% YoY</td><td><span class="tag">HIGH</span></td></tr>
  <tr><td>Community Platforms</td><td>$2.4B</td><td>+22% YoY</td><td><span class="tag">HIGH</span></td></tr>
  <tr><td>Wellness & Conscious Living</td><td>$5.8B</td><td>+11% YoY</td><td><span class="tag">MEDIUM</span></td></tr>
</table>

<h2>Consumer Insights</h2>
<div class="section-grid">
  <div class="card">
    <h3>Primary Demographic</h3>
    <p>Urban creatives, 25-40, high cultural literacy. They index high on independent media, art, design, and travel content. Income: $45K-120K.</p>
  </div>
  <div class="card">
    <h3>Decision Drivers</h3>
    <p>Authenticity (87%), community belonging (73%), aesthetic quality (91%), cultural cachet (68%), exclusivity without elitism (62%).</p>
  </div>
  <div class="card">
    <h3>Discovery Channels</h3>
    <p>Word of mouth (42%), Instagram (28%), cultural newsletters (15%), curated playlists (10%), in-person events (5%).</p>
  </div>
  <div class="card">
    <h3>Spending Behavior</h3>
    <p>Willing to pay premium for quality experiences. Average event spend: $75-150. Membership fee tolerance: $15-40/month.</p>
  </div>
</div>

<h2>Threats & Barriers</h2>
<ul>
  <li><strong>Market Saturation:</strong> Many entrants in the "elevated experience" space, though few execute with depth.</li>
  <li><strong>Dependence on Physical:</strong> Economic downturns or health crises can impact event-based models.</li>
  <li><strong>Cultural Appropriation Risk:</strong> Brands mixing cultures without depth face backlash.</li>
  <li><strong>Scaling Authenticity:</strong> The tension between growth and maintaining genuine community feel.</li>
</ul>

<hr>
<p style="font-size:0.78rem; color:#706b5e;">This analysis is template-generated and should be validated against real market data for {name}.</p>
""")

def generate_competitor_analysis_html(name: str, brief: str) -> str:
    return _doc_shell(f"Competitive Analysis — {name}", "Strategist", f"""
<div class="highlight"><p>Mapping the competitive landscape for <strong>{name}</strong> to identify positioning opportunities and strategic gaps.</p></div>

<h2>Direct Competitors</h2>
<table>
  <tr><th>Brand</th><th>Positioning</th><th>Strengths</th><th>Weaknesses</th><th>Threat Level</th></tr>
  <tr>
    <td><strong>Soho House</strong></td>
    <td>Members-only creative club</td>
    <td>Global brand, strong identity, premium venues</td>
    <td>Exclusive to fault, perceived elitism, aging model</td>
    <td><span class="tag">HIGH</span></td>
  </tr>
  <tr>
    <td><strong>Daybreaker</strong></td>
    <td>Conscious morning parties</td>
    <td>Wellness positioning, community-first, Instagram-ready</td>
    <td>Niche, limited revenue diversification, event-dependent</td>
    <td><span class="tag">MEDIUM</span></td>
  </tr>
  <tr>
    <td><strong>Secret Cinema</strong></td>
    <td>Immersive entertainment</td>
    <td>High production value, strong storytelling, cult following</td>
    <td>High cost, infrequent events, IP-dependent</td>
    <td><span class="tag">MEDIUM</span></td>
  </tr>
  <tr>
    <td><strong>The Wing / Alma</strong></td>
    <td>Identity-based community space</td>
    <td>Strong mission, engaged community, content arm</td>
    <td>Operational challenges, narrow demographics</td>
    <td><span class="tag">LOW</span></td>
  </tr>
</table>

<h2>Indirect Competitors</h2>
<table>
  <tr><th>Brand</th><th>Category</th><th>Overlap</th></tr>
  <tr><td>Spotify Live Events</td><td>Music & Discovery</td><td>Audience curation, cultural programming</td></tr>
  <tr><td>Burning Man / Meow Wolf</td><td>Immersive Art</td><td>Experience-first, community, counter-culture</td></tr>
  <tr><td>Patreon / Geneva</td><td>Community Platforms</td><td>Membership models, creator economy</td></tr>
</table>

<h2>Competitive Positioning Map</h2>
<div class="section-grid">
  <div class="card">
    <h3>Axis 1: Exclusivity</h3>
    <div class="bar"><div class="bar-fill" style="width:35%"></div></div>
    <p>Low → High exclusivity. {name} should position in the mid-range: curated but not gatekept.</p>
  </div>
  <div class="card">
    <h3>Axis 2: Cultural Depth</h3>
    <div class="bar"><div class="bar-fill" style="width:85%"></div></div>
    <p>Shallow → Deep. Key differentiator for {name}: most competitors optimize for surface aesthetics.</p>
  </div>
  <div class="card">
    <h3>Axis 3: Digital-Physical Mix</h3>
    <div class="bar"><div class="bar-fill" style="width:55%"></div></div>
    <p>Pure physical → Pure digital. Hybrid model gives {name} resilience and reach.</p>
  </div>
  <div class="card">
    <h3>Axis 4: Scale Ambition</h3>
    <div class="bar"><div class="bar-fill" style="width:45%"></div></div>
    <p>Boutique → Mass. {name} should stay intentionally small initially, then expand selectively.</p>
  </div>
</div>

<h2>Strategic Gaps (Opportunities)</h2>
<ul>
  <li><strong>Conscious Nightlife:</strong> No major brand owns "nightlife with intention." This is {name}'s core opportunity.</li>
  <li><strong>Cultural Programming as Content:</strong> Competitors host events but don't curate ongoing cultural dialogue.</li>
  <li><strong>Artist-First Model:</strong> Most platforms extract from artists; a cooperative model could be disruptive.</li>
  <li><strong>Tiered Access Without Elitism:</strong> A transparent, values-aligned access model (not just wealth-gatekept).</li>
</ul>

<hr>
<p style="font-size:0.78rem; color:#706b5e;">Competitor data is simulated for framework purposes. Validate with actual market research for {name}.</p>
""")

def generate_brand_positioning_html(name: str, direction: str, desc: str) -> str:
    return _doc_shell(f"Brand Positioning — {name}", "Strategist", f"""
<div class="highlight"><p><strong>Chosen Direction:</strong> {direction}</p><p>{desc}</p></div>

<h2>Brand Essence</h2>
<p>{name} is not a venue, an app, or an event series. It is a <strong>cultural protocol</strong> — a shared language for people who seek depth in their nocturnal experiences. Where others optimize for volume, {name} optimizes for resonance.</p>

<h2>Positioning Statement</h2>
<div class="highlight">
  <p>For <strong>culturally engaged urbanites</strong> who believe nightlife should nourish as much as it entertains, <strong>{name}</strong> is the <strong>{direction.lower()}</strong> that transforms after-dark gathering into intentional cultural exchange. Unlike conventional nightlife brands, {name} prioritizes meaning over spectacle.</p>
</div>

<h2>Brand Architecture</h2>
<table>
  <tr><th>Layer</th><th>Element</th><th>Description</th></tr>
  <tr><td>Core</td><td>Mission</td><td>Transform nightlife into a space for conscious cultural connection</td></tr>
  <tr><td>Core</td><td>Vision</td><td>A world where after-dark experiences elevate rather than deplete</td></tr>
  <tr><td>Personality</td><td>Archetype</td><td>The Sage × The Explorer — wisdom meets adventure</td></tr>
  <tr><td>Personality</td><td>Voice</td><td>Confident, warm, culturally literate, never pretentious</td></tr>
  <tr><td>Visual</td><td>Aesthetic</td><td>Minimal luxury — dark palettes, warm metallics, organic textures</td></tr>
  <tr><td>Experience</td><td>Signature</td><td>Every event has a "threshold moment" — a deliberate transition from ordinary to extraordinary</td></tr>
</table>

<h2>Brand Pillars</h2>
<div class="section-grid">
  <div class="card">
    <h3>🎭 Curation</h3>
    <p>Every element — music, space, art, food — is intentionally selected, never algorithmically prescribed.</p>
  </div>
  <div class="card">
    <h3>🌙 Intention</h3>
    <p>Nightlife with purpose. Each gathering is designed to create genuine connection, not just consumption.</p>
  </div>
  <div class="card">
    <h3>🤝 Community</h3>
    <p>A self-selecting collective of creators, thinkers, and feelers who share values over demographics.</p>
  </div>
  <div class="card">
    <h3>✨ Craft</h3>
    <p>Excellence in every detail — from sound design to cocktail curation. The brand whispers quality.</p>
  </div>
</div>

<h2>Competitive Differentiation</h2>
<table>
  <tr><th>Dimension</th><th>Competitors</th><th>{name}</th></tr>
  <tr><td>Selection Model</td><td>Wealth-based or trend-based</td><td>Values-aligned curation</td></tr>
  <tr><td>Experience Design</td><td>Aesthetic-first</td><td>Meaning-first, aesthetic follows</td></tr>
  <tr><td>Artist Relationship</td><td>Transactional</td><td>Collaborative, co-creative</td></tr>
  <tr><td>Content Strategy</td><td>Event promotion</td><td>Ongoing cultural dialogue</td></tr>
  <tr><td>Growth Model</td><td>Scale fast</td><td>Grow deep, then expand selectively</td></tr>
</table>

<hr>
<p style="font-size:0.78rem; color:#706b5e;">This positioning framework should be validated with stakeholder interviews for {name}.</p>
""")

def generate_audience_profile_html(name: str, brief: str, direction: str) -> str:
    return _doc_shell(f"Target Audience Profile — {name}", "Strategist", f"""
<div class="highlight"><p>Understanding who {name} serves — beyond demographics, into psychographics and cultural identity.</p></div>

<h2>Primary Audience: The Cultural Creative</h2>
<table>
  <tr><th>Attribute</th><th>Detail</th></tr>
  <tr><td>Age</td><td>25-40</td></tr>
  <tr><td>Location</td><td>Major creative cities (NYC, LA, London, Berlin, Mexico City, São Paulo)</td></tr>
  <tr><td>Income</td><td>$45K-$120K — not defined by wealth but by cultural capital</td></tr>
  <tr><td>Education</td><td>Often university-educated, but self-directed learners equally represented</td></tr>
  <tr><td>Occupation</td><td>Creative industries, tech, independent professionals, founders, artists</td></tr>
</table>

<h2>Psychographic Profile</h2>
<div class="section-grid">
  <div class="card">
    <h3>Values</h3>
    <ul>
      <li>Authenticity over performance</li>
      <li>Depth over reach</li>
      <li>Community over network</li>
      <li>Craft over convenience</li>
      <li>Sustainability as baseline</li>
    </ul>
  </div>
  <div class="card">
    <h3>Behaviors</h3>
    <ul>
      <li>Discovers through word-of-mouth and curated sources</li>
      <li>Avoids mainstream nightlife and mass events</li>
      <li>Spends on experience, not status symbols</li>
      <li>Active on IG but resists performative posting</li>
      <li>Supports indie/local over corporate</li>
    </ul>
  </div>
  <div class="card">
    <h3>Media Diet</h3>
    <ul>
      <li>Resident Advisor, The Vinyl Factory, Monocle</li>
      <li>Independent podcasts, Substack newsletters</li>
      <li>Art exhibitions, independent cinema</li>
      <li>Curated Spotify mixes, Bandcamp</li>
    </ul>
  </div>
  <div class="card">
    <h3>Pain Points</h3>
    <ul>
      <li>"Nightlife feels empty and transactional"</li>
      <li>"I want to meet interesting people organically"</li>
      <li>"Most events are all aesthetic, no substance"</li>
      <li>"I'm tired of algorithm-driven discovery"</li>
    </ul>
  </div>
</div>

<h2>Audience Personas</h2>
<div class="section-grid">
  <div class="card">
    <h3>🎨 The Creator</h3>
    <p><strong>Maya, 28, Visual Artist</strong> — Seeks spaces where her work is understood, not just "cool." Values artistic integrity and genuine collaboration. Will champion {name} to her network if the experience is real.</p>
  </div>
  <div class="card">
    <h3>🧠 The Curator</h3>
    <p><strong>Daniel, 34, Music Journalist</strong> — Has impeccable taste and a wide cultural network. Wants to discover before everyone else. His endorsement is worth more than any ad campaign.</p>
  </div>
  <div class="card">
    <h3>🌍 The Nomad</h3>
    <p><strong>Léa, 31, Remote UX Designer</strong> — Lives between cities. Seeks belonging without geographic commitment. {name} is her cultural anchor in any city.</p>
  </div>
  <div class="card">
    <h3>💡 The Founder</h3>
    <p><strong>Alex, 37, Tech Entrepreneur</strong> — Bored of founder meetups. Wants intellectual stimulation in unconventional settings. Will invest in {name} if the vision is clear.</p>
  </div>
</div>

<hr>
<p style="font-size:0.78rem; color:#706b5e;">Personas are illustrative. Validate with user interviews for {name}.</p>
""")

def generate_brand_strategy_doc_html(name: str, strategy: str, brief: str) -> str:
    return _doc_shell(f"Brand Strategy Document — {name}", "Strategist", f"""
<div class="highlight"><p><strong>Approved Strategy:</strong> {strategy}</p></div>

<h2>Executive Summary</h2>
<p>{name} will enter the market as a curated cultural platform that reimagines what nightlife and gathering can mean. Rooted in the approved strategic direction of <strong>{strategy.split(':')[0] if ':' in strategy else strategy}</strong>, the brand will differentiate through intentional curation, community depth, and artistic integrity.</p>

<h2>Strategic Framework</h2>
<table>
  <tr><th>Dimension</th><th>Decision</th><th>Rationale</th></tr>
  <tr><td>Market Entry</td><td>Single-city launch → selective expansion</td><td>Build density and loyalty before scaling</td></tr>
  <tr><td>Revenue Model</td><td>Events + Membership + Brand Collaborations</td><td>Three pillars prevent single-point-of-failure</td></tr>
  <tr><td>Growth Strategy</td><td>Organic, community-led</td><td>Authentic growth preserves brand integrity</td></tr>
  <tr><td>Content Strategy</td><td>Cultural programming (editorial + events)</td><td>Content builds authority between events</td></tr>
  <tr><td>Pricing</td><td>Accessible premium ($30-80 events, $20-40/mo membership)</td><td>High enough for quality, low enough for cultural diversity</td></tr>
</table>

<h2>Go-to-Market Phases</h2>
<h3>Phase 1 — Foundation (Month 1-3)</h3>
<ul>
  <li>Brand identity system complete</li>
  <li>Website + content platform live</li>
  <li>Founding community of 100 members recruited via personal outreach</li>
  <li>3 pilot events — intimate, high-curation, invite-only</li>
</ul>

<h3>Phase 2 — Establishment (Month 4-6)</h3>
<ul>
  <li>Public launch with membership tier</li>
  <li>Monthly programming cadence established</li>
  <li>Media coverage + cultural press</li>
  <li>First brand collaboration</li>
</ul>

<h3>Phase 3 — Expansion (Month 7-12)</h3>
<ul>
  <li>Second city exploration</li>
  <li>Artist residency program</li>
  <li>Digital content arm (podcast/editorial)</li>
  <li>Revenue diversification</li>
</ul>

<h2>Risk Register</h2>
<table>
  <tr><th>Risk</th><th>Probability</th><th>Impact</th><th>Mitigation</th></tr>
  <tr><td>Scaling too fast</td><td>Medium</td><td>High</td><td>Strict capacity limits, waitlist model</td></tr>
  <tr><td>Cultural dilution</td><td>Medium</td><td>High</td><td>Curation council, community governance</td></tr>
  <tr><td>Venue dependency</td><td>High</td><td>Medium</td><td>Multi-venue partnerships, pop-up model</td></tr>
  <tr><td>Economic downturn</td><td>Low</td><td>High</td><td>Digital content pivot, lower-cost formats</td></tr>
</table>

<h2>Success Metrics (Year 1)</h2>
<div class="section-grid">
  <div class="card">
    <div class="score">500+</div>
    <p>Active members</p>
  </div>
  <div class="card">
    <div class="score">24</div>
    <p>Events produced</p>
  </div>
  <div class="card">
    <div class="score">85%</div>
    <p>Member retention rate</p>
  </div>
  <div class="card">
    <div class="score">$150K+</div>
    <p>Annual revenue</p>
  </div>
</div>

<hr>
<p style="font-size:0.78rem; color:#706b5e;">Strategy approved by founder. This document serves as the strategic North Star for all downstream creative and operational decisions.</p>
""")

def generate_visual_direction_html(name: str, strategy: str) -> str:
    return _doc_shell(f"Visual Direction Brief — {name}", "Designer", f"""
<div class="highlight"><p>Visual translation of the approved <strong>{strategy.split(':')[0] if ':' in strategy else strategy}</strong> strategy into design language.</p></div>

<h2>Design Philosophy</h2>
<p>The visual identity for {name} should feel like discovering a hidden room in a familiar building — surprising but inevitable. Every design choice should whisper sophistication without performing luxury.</p>

<h2>Color System</h2>
<table>
  <tr><th>Role</th><th>Color</th><th>Usage</th></tr>
  <tr><td>Primary Dark</td><td style="color:#0d0d0f">■</td><td>Backgrounds, immersion → #0D0D0F</td></tr>
  <tr><td>Accent Gold</td><td style="color:#c8a96e">■</td><td>Highlights, CTAs, warmth → #C8A96E</td></tr>
  <tr><td>Text Primary</td><td style="color:#e0ddd5">■</td><td>Headlines, key content → #E0DDD5</td></tr>
  <tr><td>Text Secondary</td><td style="color:#a09b8c">■</td><td>Body text, descriptions → #A09B8C</td></tr>
  <tr><td>Surface</td><td style="color:#1a1a1e">■</td><td>Cards, containers → #1A1A1E</td></tr>
  <tr><td>Accent Warm</td><td style="color:#d4a574">■</td><td>Special moments → #D4A574</td></tr>
</table>

<h2>Typography</h2>
<div class="section-grid">
  <div class="card">
    <h3>Display / Headlines</h3>
    <p>A serif or transitional typeface with character. Something that feels editorial and timeless, not trendy. Consider: Freight Display, Canela, or GT Sectra.</p>
  </div>
  <div class="card">
    <h3>Body / UI</h3>
    <p>A clean, humanist sans-serif for readability and warmth. Inter, Graphik, or Söhne. Neutral but not cold.</p>
  </div>
</div>

<h2>Photography & Art Direction</h2>
<ul>
  <li><strong>Mood:</strong> Warm darkness. Candlelit, not spotlit. Intimacy over spectacle.</li>
  <li><strong>Color Grade:</strong> Desaturated with warm undertones. No neon, no club photography aesthetics.</li>
  <li><strong>Subjects:</strong> People in genuine connection. Never posed, never performative.</li>
  <li><strong>Composition:</strong> Cinematic framing. Wide aperture, bokeh. Feels like a film still, not a marketing photo.</li>
  <li><strong>Avoid:</strong> Overhead party shots, flash photography, stock-feeling images, excessive text overlays.</li>
</ul>

<h2>Motion & Interaction</h2>
<ul>
  <li>Slow, deliberate transitions (300-500ms ease). Nothing should feel frenetic.</li>
  <li>Subtle parallax and reveal animations. Content should emerge, not jump.</li>
  <li>Hover states that feel tactile — slight scale, glow, or shift.</li>
  <li>Loading states that feel meditative, not anxious.</li>
</ul>

<h2>Logo Direction</h2>
<p>The logo should work as both a wordmark and a symbol. It needs to be recognizable at 16px (favicon) and beautiful at billboard scale. Consider custom lettering that feels hand-crafted but precise — the visual equivalent of a perfectly mixed cocktail.</p>

<h2>Key Deliverables</h2>
<table>
  <tr><th>Asset</th><th>Priority</th><th>Notes</th></tr>
  <tr><td>Logo System (wordmark + icon)</td><td><span class="tag">P1</span></td><td>Must work on dark and light backgrounds</td></tr>
  <tr><td>Brand Color Palette + Guidelines</td><td><span class="tag">P1</span></td><td>Extended palette for digital + print</td></tr>
  <tr><td>Typography Hierarchy</td><td><span class="tag">P1</span></td><td>Web + print specifications</td></tr>
  <tr><td>Social Media Templates</td><td><span class="tag">P2</span></td><td>Story, post, event announcement</td></tr>
  <tr><td>Event Collateral Templates</td><td><span class="tag">P2</span></td><td>Poster, flyer, wristband</td></tr>
  <tr><td>Website Wireframes</td><td><span class="tag">P2</span></td><td>Landing, membership, events</td></tr>
</table>

<hr>
<p style="font-size:0.78rem; color:#706b5e;">This brief serves as direction for the design team. Final creative execution should be presented for approval.</p>
""")

# --- Static Surface Layer (Studio OS) ---
# Serve specific frontend files to avoid shadowing API routes
from fastapi.responses import FileResponse

project_root = os.getcwd()

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(project_root, "index.html"))

@app.get("/index.html")
async def serve_index_file():
    return FileResponse(os.path.join(project_root, "index.html"))

@app.get("/index.css")
async def serve_css():
    return FileResponse(os.path.join(project_root, "index.css"))

@app.get("/index.js")
async def serve_js():
    return FileResponse(os.path.join(project_root, "index.js"))

# Optional: Serve studio_os directory if needed for assets, but at a specific path
if os.path.exists(os.path.join(project_root, "studio_os")):
    app.mount("/studio_os", StaticFiles(directory=os.path.join(project_root, "studio_os"), html=True), name="studio_os")

