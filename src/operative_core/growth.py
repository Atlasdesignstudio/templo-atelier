from typing import Dict, Any

def growth_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chief Growth Officer
    Role: Simulates lead intake.
    """
    print("--- [Agent] Chief Growth Officer: New Lead Acquired ---")
    
    # In a real app, this would come from a webhook or scraping
    return {
        "client_brief": state.get("client_brief", "Default Brief"),
        "project_budget_tokens": 1000.0 # Assign initial budget
    }
