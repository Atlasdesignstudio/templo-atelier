"""Seed rich data for all 6 projects: documents, tasks, workflow steps, agent logs."""
import requests, json
from datetime import datetime, timedelta

API = "http://localhost:8000"

# --- Documents (via direct DB since no create endpoint) ---
# We'll create them through the run-strategy endpoint or a quick SQL approach.
# Instead, let's use the workflow seed endpoint that already exists.

# Seed tasks
tasks = [
    # Project 1: Atlas Launch
    {"title": "Finalize brand positioning", "priority": "High", "project_id": 1},
    {"title": "Approve color palette", "priority": "Normal", "project_id": 1},
    {"title": "Review logo concepts", "priority": "High", "project_id": 1},
    # Project 2: Vera Cosmetics
    {"title": "Define target audience personas", "priority": "High", "project_id": 2},
    {"title": "Review packaging mockups", "priority": "Normal", "project_id": 2},
    {"title": "Approve typography selection", "priority": "Normal", "project_id": 2},
    # Project 3: Meridian Web
    {"title": "Wireframe homepage layout", "priority": "High", "project_id": 3},
    {"title": "Review responsive breakpoints", "priority": "Normal", "project_id": 3},
    {"title": "Set up CMS integration", "priority": "Normal", "project_id": 3},
    # Project 4: Lumen App
    {"title": "User testing session #1", "priority": "High", "project_id": 4},
    {"title": "Fix accessibility issues", "priority": "High", "project_id": 4},
    {"title": "Prepare handoff documentation", "priority": "Normal", "project_id": 4},
    # Project 5: Nova Packaging
    {"title": "3D render bottle design", "priority": "High", "project_id": 5},
    {"title": "Select print vendor", "priority": "Normal", "project_id": 5},
    # Project 6: Prism Controller
    {"title": "Industrial design sketches", "priority": "High", "project_id": 6},
    {"title": "Material selection research", "priority": "Normal", "project_id": 6},
    {"title": "Ergonomics study", "priority": "High", "project_id": 6},
]

# Seed agent logs
logs = [
    {"project_id": 1, "agent_name": "Strategist", "message": "Project initialized. Beginning brand audit."},
    {"project_id": 1, "agent_name": "Director", "message": "Assigned Strategist agent to lead synthesis phase."},
    {"project_id": 1, "agent_name": "CFO", "message": "Budget allocated: $12,000. Margin target: 40%."},
    {"project_id": 2, "agent_name": "Strategist", "message": "Clean beauty market analysis complete."},
    {"project_id": 2, "agent_name": "Designer", "message": "Moodboard created with 24 reference images."},
    {"project_id": 3, "agent_name": "Strategist", "message": "Competitor web audit: 5 firms analyzed."},
    {"project_id": 3, "agent_name": "Director", "message": "Timeline set: 6-week sprint to launch."},
    {"project_id": 4, "agent_name": "Designer", "message": "Patient dashboard v2 prototype complete."},
    {"project_id": 4, "agent_name": "CFO", "message": "Project at 85% budget. Delivery on track."},
    {"project_id": 5, "agent_name": "Strategist", "message": "Shelf presence analysis: premium tier positioning."},
    {"project_id": 6, "agent_name": "Director", "message": "Product design brief finalized. R&D phase begins."},
    {"project_id": 6, "agent_name": "Strategist", "message": "Competitive DJ controller market mapped."},
]

print("Seeding tasks...")
for t in tasks:
    due = (datetime.utcnow() + timedelta(days=7)).isoformat()
    r = requests.post(f"{API}/tasks/", json={
        "title": t["title"], "priority": t["priority"],
        "project_id": t["project_id"], "status": "Todo",
        "due_date": due
    })
    print(f"  Task: {t['title']} -> {r.status_code}")

print("\nSeeding agent logs...")
for l in logs:
    r = requests.post(f"{API}/logs/", json={
        "project_id": l["project_id"],
        "agent_name": l["agent_name"],
        "message": l["message"],
        "severity": "INFO",
        "cost_incurred": 0.0,
    })
    print(f"  Log: {l['agent_name']}: {l['message'][:40]}... -> {r.status_code}")

# Seed documents — we need to check if there's a direct endpoint
# Try the workflow seed endpoint for a project
print("\nSeeding workflow steps via API...")
for pid in [1, 2, 3, 4, 5, 6]:
    r = requests.post(f"{API}/founder/project/{pid}/workflow/seed")
    print(f"  Workflow seed P{pid} -> {r.status_code}")

print("\n✓ All seed data inserted.")
