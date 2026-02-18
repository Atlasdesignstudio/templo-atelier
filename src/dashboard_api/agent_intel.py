import os
import json
from google import genai  # type: ignore
from typing import List, Dict, Any, Optional

# Initialize shared client if key exists
try:
    from ._secrets import GEMINI_API_KEY_FALLBACK  # type: ignore
except ImportError:
    GEMINI_API_KEY_FALLBACK = None

api_key = os.environ.get("GEMINI_API_KEY") or GEMINI_API_KEY_FALLBACK
client = genai.Client(api_key=api_key) if api_key else None

def _clean_json(text: str) -> str:
    """Extract JSON from markdown code blocks if present."""
    text = str(text).strip()
    if text.startswith("```json"):
        text = text.replace("```json", "", 1)
    # Use removesuffix to avoid slicing issues in Pyre
    if text.endswith("```"):
        text = text.removesuffix("```")
    return text.strip()

def generate_roadmap_llm(project_name: str, brief: str) -> List[Dict[str, Any]]:
    """
    Generates a 4-phase project roadmap (Discovery, Strategy, Design, Production) 
    with 20+ specific tasks tailored to the brief.
    """
    if not client:
        return _fallback_roadmap()

    # Enable Search Tool (Grounding) if available in this environment
    # Note: genai SDK usage for tools varies by version. Using standard prompt engineering for specificity first.
    
    prompt = f"""
    Act as a Senior Project Manager & Strategist.
    Project: {project_name}
    Brief: {brief}

    Task: Create a detailed, 4-phase project roadmap (Discovery, Strategy, Design, Production).
    
    CRITICAL: 
    - Do NOT use generic tasks like "Market Research" or "Design Logo".
    - Be extremely specific to the industry and brief. 
    - Example for a Coffee Shop: "Scout locations in high-foot-traffic hipster neighborhoods", "Taste test 5 bean varieties", "Design takeaway cup packaging".
    - Example for a Tech SaaS: "Audit competitor API documentation", "Design user onboarding flow", "Stress test database schema".
    
    Generate exactly 20-25 tasks.
    Return a JSON array of objects with:
    - "title": Specific task name (e.g. "Conduct taste test with 50 locals")
    - "phase": "Discovery", "Strategy", "Design", or "Production"
    - "days": Integer (days from start, e.g. 1, 3, 10, 30). Space them out realistically over 4 weeks.
    - "prio": "High" or "Normal"

    Output JSON only.
    """
    
    try:
        # Use tools='google_search_retrieval' if we want grounding, 
        # but for roadmap generation, pure reasoning is often better tailored than search results.
        # We will key "Research" tasks to search later.
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return json.loads(_clean_json(response.text))
    except Exception as e:
        print(f"LLM Error (Roadmap): {e}")
        return _fallback_roadmap()

def _fallback_roadmap():
    return [
        {"title": "Deep Dive Discovery Session", "phase": "Discovery", "days": 1, "prio": "High"},
        {"title": "Competitor Audit", "phase": "Discovery", "days": 2, "prio": "Normal"},
        {"title": "Define Brand Archetypes", "phase": "Strategy", "days": 5, "prio": "High"},
        {"title": "Visual Identity Exploration", "phase": "Design", "days": 10, "prio": "High"},
        {"title": "Finalize Brand Guidelines", "phase": "Production", "days": 20, "prio": "Normal"}
    ]

def generate_strategic_directions_llm(project_name: str, brief: str) -> List[Dict[str, str]]:
    """
    Generates 3 distinct strategic directions based on the project brief.
    """
    if not client:
        return _fallback_directions(project_name)

    prompt = f"""
    You are a world-class Brand Strategist.
    Project Name: {project_name}
    Client Brief: {brief}

    Task: Analyze the brief and identify 3 distinct strategic directions for this brand.
    Each direction should take the brand in a fundamentally different way (e.g., one focused on heritage, one on innovation, one on community).
    
    Return a JSON array of 3 objects. Each object must have:
    - "key": "A", "B", or "C"
    - "title": Short, evocative title (2-4 words)
    - "description": 2-3 sentences explaining the direction, its focus, and the vibe.

    Output JSON only.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return json.loads(_clean_json(response.text))
    except Exception as e:
        print(f"LLM Error (Directions): {e}")
        return _fallback_directions(project_name)

def _fallback_directions(project_name: str):
    return [
        {"key": "A", "title": "Market Leader", "description": f"Position {project_name} as the premium authority in the space."},
        {"key": "B", "title": "Disruptor", "description": f"Challenge the status quo with a bold, unexpected approach for {project_name}."},
        {"key": "C", "title": "Community-First", "description": f"Build {project_name} around deep connection and shared values."}
    ]

def expand_strategy_llm(project_name: str, brief: str, chosen_direction: Dict[str, str]) -> Dict[str, Any]:
    """
    Expands a chosen direction into a full strategic framework.
    """
    if not client:
        return _fallback_strategy(project_name, chosen_direction)

    prompt = f"""
    You are a Chief Strategy Officer.
    Project: {project_name}
    Brief: {brief}
    Chosen Strategic Direction: "{chosen_direction['title']}" - {chosen_direction['description']}

    Task: Expand this direction into a concrete brand strategy.
    
    Return a JSON object with:
    - "positioning": A single powerful positioning statement.
    - "pillars": Array of 3 short brand pillars (e.g., "Radical Transparency").
    - "tensions": Array of 3 strategic tensions (e.g., "Heritage vs. Innovation").
    - "principles": Array of 3 design principles (e.g., "Bold but Quiet").

    Output JSON only.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return json.loads(_clean_json(response.text))
    except Exception as e:
        print(f"LLM Error (Strategy Expansion): {e}")
        return _fallback_strategy(project_name, chosen_direction)

def _fallback_strategy(project_name, direction):
    return {
        "positioning": f"{project_name} is the definitive choice for the modern era.",
        "pillars": ["Quality First", "Customer Obsession", "Sustainable Core"],
        "tensions": ["Global vs Local", "Premium vs Accessible", "Timeless vs Modern"],
        "principles": ["Simplicity", "Clarity", "Warmth"]
    }

def generate_research_doc_content(doc_type: str, project_name: str, brief: str, strategy_context: str = "") -> str:
    """
    Generates HTML content for research documents.
    """
    if not client:
        return f"<p>LLM unavailable. Mock content for {doc_type} based on {brief}</p>"

    prompts = {
        "market_landscape": f"""
            Analyze the market landscape for {project_name} ({brief}). 
            Cover: Industry Trends, Market Shifts, and Opportunities.
            Output as semantic HTML (no <html> definition, just body content: <h2>, <p>, <ul>).
            Keep it professional, insightful, and concise.
        """,
        "competitor_analysis": f"""
            Analyze potential competitors for {project_name} ({brief}).
            Identify 3 archetypal competitors (Direct, Indirect, Aspirational).
            Output as semantic HTML (no <html> definition, just body content).
        """,
        "target_audience": f"""
            Create a Target Audience Profile for {project_name}.
            Context: {strategy_context}
            Cover: Demographics, Psychographics, Pain Points, and "A Day in the Life".
            Output as semantic HTML.
        """,
        "brand_positioning": f"""
            Draft a Brand Positioning Report for {project_name}.
            Strategy: {strategy_context}
            Cover: The "Why", The "How", and The "What".
            Output as semantic HTML.
        """
    }
    
    requested_prompt = prompts.get(doc_type, f"Write a {doc_type} for {project_name}")

    try:
        # Enable Google Search Grounding for deep research
        # This forces the model to use Google Search to find current info.
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{requested_prompt}\nReturn ONLY clean HTML tags.",
            config={
                'tools': [{'google_search': {}}]
            }
        )
        return _clean_html(response.text)
    except Exception as e:
        print(f"LLM Error (Doc Gen - {doc_type}): {e}")
        return f"<p>Error generating content: {e}</p>"

def _clean_html(text: str) -> str:
    text = str(text).strip()
    if text.startswith("```html"):
        text = text.replace("```html", "", 1)
    elif text.startswith("```"):
        text = text.replace("```", "", 1)
    
    if text.endswith("```"):
        text = text.removesuffix("```")
    return text.strip()

def _safe_sub(a: int, b: int) -> int:
    return int(a - b)

def recommend_deliverables_llm(project_name: str, brief: str, budget: int, all_deliverables: List[Dict]) -> List[str]:
    """
    Selects the best deliverables from the catalog based on the brief and budget.
    """
    if not client:
        # Fallback: simple fit
        return [str(d["key"]) for d in all_deliverables if int(d.get("cost", 0)) <= budget]

    catalog_str = json.dumps([{"key": d["key"], "name": d.get("name", d.get("title", "Unknown")), "cost": d["cost"]} for d in all_deliverables])
    
    prompt = f"""
    Project: {project_name}
    Brief: {brief}
    Budget: ${budget}
    
    Available Catalog:
    {catalog_str}
    
    Task: Select the optimal set of deliverables that fit within the ${budget} budget and best serve the brief.
    Prioritize core assets needed for this specific project type.
    
    Return a JSON array of strings (keys only). Example: ["LOGO", "WEBSITE"]
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return json.loads(_clean_json(response.text))
    except Exception as e:
        print(f"LLM Error (Deliverables): {e}")
        # Use fallback if LLM fails
        return _fallback_deliverables(budget, all_deliverables)

def _fallback_deliverables(budget: int, all_deliverables: List[Dict]) -> List[str]:
    selected: List[str] = []
    r_val: int = 0
    try:
        r_val = int(budget)
    except (ValueError, TypeError):
        r_val = 0

    for d in all_deliverables:
        c_val: int = 0
        try:
            c_val = int(d.get("cost", 0))
        except (ValueError, TypeError):
            c_val = 0

        if c_val <= r_val:
            selected.append(str(d.get("key", "")))
            r_val = _safe_sub(r_val, c_val)
    return selected
