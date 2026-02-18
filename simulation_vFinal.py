import requests
import json
import time

BASE_URL = "http://localhost:8000"

def log(msg):
    print(f"[Simulation] {msg}")

def run_simulation():
    log("Starting End-to-End Simulation of Templo Atelier vFinal...")
    
    # 1. Create Project (Activates Economics)
    log("Creating Project 'Simulation Beta'...")
    try:
        resp = requests.post(f"{BASE_URL}/projects/", json={
            "name": "Simulation Beta",
            "client_brief": "A neobank for Gen Z gamers.",
            "budget_cap": 8000
        })
        if resp.status_code != 200:
            log(f"Failed to create project: {resp.text}")
            return
        
        project = resp.json()
        pid = project["project_id"]
        log(f"✅ Project Created: ID {pid}")
    except Exception as e:
        log(f"Failed to connect to API: {e}")
        return

    # 2. Seed Workflow (Activates Orchestrator / Director)
    log("Seeding Workflow...")
    resp = requests.post(f"{BASE_URL}/founder/project/{pid}/workflow/seed")
    if resp.status_code != 200:
        log(f"Failed to seed: {resp.text}")
        return
    log("✅ Workflow Seeded.")

    # 3. Resolve 'Project Brief' (Activates Strategist)
    # We need to find the step ID first.
    resp = requests.get(f"{BASE_URL}/founder/project/{pid}/workflow")
    steps = resp.json()
    brief_step = next((s for s in steps if s["title"] == "Project Brief"), None)
    
    if not brief_step:
        log("❌ 'Project Brief' step not found!")
        return

    log(f"Resolving Brief (Step {brief_step['id']})... triggering Strategist...")
    resp = requests.post(f"{BASE_URL}/founder/project/{pid}/workflow/resolve", json={
        "step_id": brief_step["id"],
        "action": "input",
        "input_text": "A banking app that feels like a video game UI. Dark mode default. Loot boxes for savings."
    })
    
    if resp.status_code != 200:
        log(f"Failed to resolve brief: {resp.text}")
        return
    
    time.sleep(2) # Wait for processing if async (vFinal acts sync currently)
    
    # 4. Check for 'Strategic Direction' Step (Output of Strategist)
    resp = requests.get(f"{BASE_URL}/founder/project/{pid}/workflow")
    start_time = time.time()
    direction_step = None
    
    # Poll for result (simulating async nature, though Python is sync here)
    while time.time() - start_time < 10:
        steps = resp.json()
        direction_step = next((s for s in steps if s["title"] == "Strategic Direction"), None)
        if direction_step:
            break
        time.sleep(1)
        resp = requests.get(f"{BASE_URL}/founder/project/{pid}/workflow")

    if not direction_step:
        log("❌ Strategist failed to generate directions in time.")
        return
    
    options = direction_step.get("options", [])
    log(f"✅ Strategist Generated {len(options)} Directions.")
    log(f"   Option A: {options[0].get('title')}")

    # 5. Resolve Direction (Activates Strategist Expand)
    log(f"Selecting Option A (Step {direction_step['id']})... triggering Expansion...")
    resp = requests.post(f"{BASE_URL}/founder/project/{pid}/workflow/resolve", json={
        "step_id": direction_step["id"],
        "action": "choose",
        "chosen_option": "A"
    })
    
    # 6. Check for Review Step
    resp = requests.get(f"{BASE_URL}/founder/project/{pid}/workflow")
    review_step = next((s for s in resp.json() if s["title"] == "Strategy Review"), None)
    
    if review_step:
        log("✅ Strategy Expanded and Ready for Review.")
        # Approve it to trigger Deliverables
        log("Approving Strategy... triggering Director...")
        requests.post(f"{BASE_URL}/founder/project/{pid}/workflow/resolve", json={
            "step_id": review_step["id"],
            "action": "approve"
        })
        
        # Check Deliverables
        resp = requests.get(f"{BASE_URL}/founder/project/{pid}/workflow")
        deliv_step = next((s for s in resp.json() if s["title"] == "Deliverable Selection"), None)
        if deliv_step:
            log("✅ Director Recommended Deliverables.")
            opts = deliv_step.get("options", [])
            selected = [o['title'] for o in opts if o.get('selected')]
            log(f"   Auto-Selected: {selected}")
        else:
            log("❌ Director failed to recommend deliverables.")

    else:
        log("❌ Strategy Expansion failed.")

    log("\n✅ SIMULATION COMPLETE.")

if __name__ == "__main__":
    run_simulation()
