from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field # type: ignore

# --- Domain Models ---

class BrandDNA(BaseModel):
    """
    The core strategic DNA of the brand.
    """
    name: str = Field(description="The agreed name of the brand.")
    tagline: str = Field(description="A punchy, memorable tagline.")
    mission: str = Field(description="The brand's core mission statement.")
    archetype: str = Field(description="The brand archetype (e.g., The Creator, The Ruler).")
    core_values: List[str] = Field(description="List of 3-5 core values.")
    target_audience: str = Field(description="Description of the primary demographic/psychographic.")
    
    # Visual Direction
    color_palette_hex: List[str] = Field(description="List of 3-5 hex codes.")
    typography_primary: str = Field(description="Name of primary font (Google Fonts).")
    typography_secondary: str = Field(description="Name of secondary font.")
    visual_style_prompt: str = Field(description="A detailed prompt describing the visual style.")

class SocialPost(BaseModel):
    platform: str
    content_type: str 
    caption: str
    hashtags: List[str]
    image_prompt: Optional[str] = None

# --- Studio State ---

class StudioState(TypedDict):
    """
    The shared state of the AI Studio.
    """
    # Operative Data
    project_id: int
    project_name: str
    methodology: str
    client_brief: str
    project_budget_tokens: float # The "Bank"
    project_status: str
    integrator: Optional[Any] # Reference to the Integrator Agent
    
    # Creative Data
    brand_dna_json: Optional[Dict[str, Any]]
    market_research: Optional[str]
    critic_feedback: Optional[str] # Feedback from the Critic agent
    cycle_count: int # To prevent infinite loops
    executive_summary: Optional[str] # Synthesized debrief for the director
    clarifying_questions: List[str] # Questions for missing info
    is_complete: bool # Flag for the gatekeeper
    
    # Metadata
    logo_svg_path: Optional[str]
    brand_visuals_paths: List[str]
    brandbook_pdf_path: Optional[str]
    social_calendar_csv: Optional[str]
    packaging_files_paths: List[str]
    figma_design_url: Optional[str]
    motion_assets_paths: List[str]
    
    # Feedback
    feedback_history: List[str]
