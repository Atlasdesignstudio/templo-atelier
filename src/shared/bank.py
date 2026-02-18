class StudioBank:
    """
    Manages the token/dollar budget for the project.
    Used by the CFO Agent to approve/deny requests.
    """
    def __init__(self, initial_budget: float):
        self.balance = initial_budget

    def check_funds(self, cost: float) -> bool:
        return self.balance >= cost

    def deduct(self, cost: float):
        if self.check_funds(cost):
            self.balance -= cost
            return True
        return False

# Pricing Table (2026 Estimated Costs)
COST_TABLE = {
    "strategy_o1": 2.0,
    "image_flux_pro": 0.5,
    "video_runway_gen4": 15.0,
    "video_luma_ray2": 4.0,
    "figma_galileo": 3.0,
    
    # Service Pricing (Client Facing)
    "service_branding_package": 850.0,
    "service_web_ux_design": 1200.0,
    "service_social_campaign": 450.0,
    "service_market_research": 300.0,
    
    # Internal Overhead (per agent pass)
    "internal_agent_overhead": 15.0 
}
