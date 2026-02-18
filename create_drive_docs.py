"""
Templo Atelier — Google Drive Business Documentation Generator
==============================================================
Creates the complete folder structure and populates Google Docs
in the user's Google Drive account.

Prerequisites:
    1. Go to https://console.cloud.google.com/apis/credentials
    2. Create an OAuth 2.0 Client ID (Desktop app)
    3. Download the JSON and save it as 'credentials.json' in this directory
    4. Enable the Google Drive API and Google Docs API in your project
    5. Run this script: python create_drive_docs.py
"""

import os
import sys
import json
from typing import Optional, Dict, List, Any

# Resolve imports for both IDE and Runtime
import sys
import os
sys.path.append(os.getcwd())

from src.shared.drive_utils import (  # type: ignore
    get_credentials, 
    get_drive_service, 
    get_docs_service, 
    ensure_folder as find_or_create_folder,
    create_google_doc
)


def authenticate():
    return get_credentials()

def get_services(creds):
    return get_drive_service(creds), get_docs_service(creds)



# Removed redundant find_or_create_folder and create_google_doc (now imported)



# ============================================================
# DOCUMENT CONTENT
# ============================================================

DOCS = {
    # --- 00_Company ---
    "Company Overview": """
TEMPLO ATELIER — COMPANY OVERVIEW
==================================

WHO WE ARE
-----------
Templo Atelier is a 1-person AI-native creative studio, powered by a constellation of specialized AI agents. We deliver world-class branding, design, motion graphics, and digital experiences — at the speed and scale that was previously impossible.

Founded in 2026, we represent the new paradigm: a single human director orchestrating an army of AI specialists to deliver enterprise-grade creative output.

BUSINESS MODEL
--------------
• Solo operator + AI agent workforce
• Per-project billing with transparent cost tracking
• Budget-conscious: agents auto-negotiate quality tiers based on project budget
• All creative output is AI-generated and human-approved

OUR EDGE
--------
• End-to-end delivery: from client brief to final assets in hours, not weeks
• Real-time observability: every agent action is logged and auditable
• Self-optimizing: a Chief Process Officer agent continuously audits performance
• Cost transparency: exact API costs tracked per project

CONTACT
-------
• Director: Mathias Meneses
• Email: mathiasmdesign@gmail.com
""",

    "Mission & Vision": """
TEMPLO ATELIER — MISSION & VISION
====================================

MISSION
-------
To democratize world-class creative services by harnessing AI agents, making premium design accessible to every business regardless of size.

VISION
------
A future where a single creative director, empowered by AI, delivers the output of an entire agency — faster, smarter, and more affordably.

VALUES
------
1. CRAFT — Every pixel matters. AI generates, but quality is non-negotiable.
2. TRANSPARENCY — Clients see real costs, real timelines, real-time progress.
3. AUTONOMY — Our agents self-organize, self-optimize, and self-correct.
4. EFFICIENCY — No wasted tokens, no wasted time, no wasted budget.
5. INNOVATION — We build the tools that build the future.
""",

    "Service Catalog": """
TEMPLO ATELIER — SERVICE CATALOG
==================================

1. BRAND STRATEGY & IDENTITY
   Agent: Chief Strategy Agent
   Deliverables:
   • Brand DNA document (name, tagline, mission, archetype, values)
   • Color palette (3-5 hex codes)
   • Typography system (primary + secondary fonts)
   • Visual style direction prompt
   Tech: Google Gemini 1.5 Pro

2. VISUAL IDENTITY DESIGN
   Agent: Visual Stylist Agent
   Deliverables:
   • Logo design (SVG, 4 variants)
   • Hero visuals and brand imagery
   • Complete brandbook (PDF)
   Tech: Flux Pro (image generation)

3. UI/UX DESIGN
   Agent: UI Architect Agent
   Deliverables:
   • High-fidelity Figma design system
   • Production-ready components
   Tech: Galileo AI / Figma API

4. SOCIAL MEDIA CAMPAIGNS
   Agent: Social Growth Agent
   Deliverables:
   • Monthly content calendars (CSV)
   • Platform-specific captions and hashtags
   • Image prompts for visual generation
   Tech: Gemini (text generation)

5. PACKAGING DESIGN
   Agent: Packaging Agent
   Deliverables:
   • 3D box/package mockups (GLB format)
   • Print-ready packaging layouts
   Tech: 3D rendering pipeline

6. MOTION GRAPHICS & VIDEO
   Agent: Motion Choreographer Agent
   Deliverables:
   • Promotional videos (4K or 720p)
   • Animated brand reveals
   • Social media video assets
   Tech: Runway Gen-4 (premium) or Luma Ray 2 (economy)
   Note: Auto-downgrades based on available budget
""",

    "Pricing & Cost Structure": """
TEMPLO ATELIER — PRICING & COST STRUCTURE
============================================

API COST TABLE (2026 Estimates)
-------------------------------
• Strategy (Gemini 1.5 Pro):     $2.00 per run
• Image Generation (Flux Pro):   $0.50 per image
• Video (Runway Gen-4 Premium):  $15.00 per clip
• Video (Luma Ray 2 Economy):    $4.00 per clip
• UI Design (Galileo/Figma):     $3.00 per design

BUDGET MANAGEMENT
-----------------
Every project gets a token budget (in USD equivalent). The CFO Agent:
• Reviews budget before each creative phase
• Auto-approves low-cost operations (text generation)
• Requires human approval for high-cost operations (video)
• Downgrades quality tier if budget is low (e.g., Runway → Luma)

EXAMPLE PROJECT BUDGET ($1,000)
-------------------------------
  Strategy:          $2.00
  Logo (4 variants): $2.00
  Hero images:       $1.50
  Figma design:      $3.00
  Social content:    $4.00
  Promo video:       $15.00
  Total API cost:    ~$27.50
  Remaining:         ~$972.50

  Note: The vast majority of budget is available for iterations,
  additional assets, and premium upgrades.
""",

    # --- 01_Operations ---
    "Intake Process": """
TEMPLO ATELIER — INTAKE PROCESS
==================================

OVERVIEW
--------
The Intake Agent is the first point of contact. It monitors a Google Drive folder for new client transcripts (meeting notes, briefs, emails) and automatically processes them into structured projects.

WORKFLOW
--------
1. TRIGGER: New file appears in Drive trigger folder
2. EXTRACT: Gemini 1.5 Pro analyzes the transcript
   → Extracts: project name, client goals, deliverables, deadlines, budget hint
3. SCAFFOLD: Creates project folder structure:
   /projects/{Year}/{Project_Name}/
     ├── 00_Intake/
     ├── 01_Strategy/
     ├── 02_Design/
     ├── 03_Finance/
     └── 99_Delivery/
4. ASSIGN: Maps deliverables to required agents
   → "brand identity" → Strategist + Stylist
   → "social media" → Social Growth Agent
   → "app design" → UI Architect
5. MISSION: Creates .antigravity/mission file (YAML)
6. PROPOSAL: Auto-generates Initial Proposal document

FALLBACK
--------
If Gemini API is unavailable, uses keyword-based parsing:
• Looks for "Project:", "Goals:", "Deliverables:", "Deadlines:", "Budget:" sections
""",

    "Client Onboarding Checklist": """
TEMPLO ATELIER — CLIENT ONBOARDING CHECKLIST
================================================

□ Receive client brief / meeting transcript
□ Intake Agent processes and extracts project context
□ Review auto-generated Initial Proposal
□ Confirm deliverables list with client
□ Set budget cap for the project
□ CFO Agent approves initial budget allocation
□ Strategist Agent generates Brand DNA
□ Human director reviews Brand DNA before creative phase
□ Creative agents execute in parallel:
   □ Visual Stylist → Logo + Brand Assets
   □ UI Architect → Figma Design
   □ Social Growth → Campaign Calendar
   □ Packaging → 3D Mockups
   □ Motion → Video Assets
□ Quality review of all deliverables
□ Package final assets in 99_Delivery folder
□ Client handoff
""",

    "Budget Management": """
TEMPLO ATELIER — BUDGET MANAGEMENT (CFO AGENT)
==================================================

ROLE
----
The CFO Agent acts as the financial gatekeeper. Before any creative agent runs an expensive operation, the CFO checks if sufficient budget remains.

LOGIC
-----
1. Each project starts with a budget (in USD)
2. Before each agent runs, it checks StudioBank.check_funds(cost)
3. If funds available → Execute and deduct
4. If funds insufficient:
   a. Try cheaper alternative (e.g., Luma instead of Runway)
   b. If no alternative → Skip and log ERROR
   c. Set project status to "Paused: Budget Exceeded"

STUDIO BANK CLASS
-----------------
• check_funds(cost) → Returns True/False
• deduct(cost) → Deducts from balance
• balance → Current remaining budget

ECONOMY MODE
------------
When balance < $50:
• CFO flags "Low Budget" warning
• Agents auto-switch to cheaper model tiers
• High-cost operations require explicit human approval
""",

    "API Cost Table": """
TEMPLO ATELIER — API COST TABLE (2026)
=========================================

SERVICE                  | PROVIDER      | COST PER UNIT
---------------------------------------------------------
Text Strategy            | Gemini 1.5 Pro| $2.00 / run
Image Generation         | Flux Pro      | $0.50 / image
Video (Premium)          | Runway Gen-4  | $15.00 / clip
Video (Economy)          | Luma Ray 2    | $4.00 / clip
UI/UX Design             | Galileo/Figma | $3.00 / design
Text Content (Social)    | Gemini Flash  | ~$0.01 / call
Email Sending            | Gmail API     | Free
File Storage             | Google Drive  | Free (within quota)
Calendar Events          | Calendar API  | Free

NOTES:
• All costs are estimates and may vary with usage volume
• Budget tracking is per-project, not per-agent
• The CFO Agent has real-time visibility into spend
""",

    "Lead Generation Process": """
TEMPLO ATELIER — LEAD GENERATION (GROWTH AGENT)
==================================================

ROLE
----
The Chief Growth Officer agent handles initial lead acquisition. Currently simulates lead intake, but designed to support:

FUTURE INTEGRATIONS
-------------------
• Webhook listeners (Calendly, Typeform, etc.)
• Email parsing (Gmail API integration ready)
• Social media DM monitoring
• Website contact form processing

CURRENT FLOW
------------
1. Growth Agent receives trigger (manual or automated)
2. Assigns default brief from lead data
3. Sets initial project budget ($1,000 default)
4. Hands off to CFO Agent for budget approval
5. CFO → Strategist → Creative pipeline begins
""",

    "API Registry": """
TEMPLO ATELIER — API REGISTRY (INTEGRATOR AGENT)
====================================================

OVERVIEW
--------
The Integrator Agent centralizes all external API connections.
Located at: src/operative_core/integrator.py

REGISTERED INTEGRATIONS
------------------------

1. GEMINI (google.genai)
   Status: ✅ Live
   Model: gemini-2.0-flash
   Actions:
   • generate_content — Text/content generation
   Auth: API Key (GEMINI_API_KEY in .env)

2. GOOGLE DRIVE
   Status: ✅ Connected (stub for full OAuth)
   Actions:
   • upload_file — Upload files to Drive
   Auth: OAuth2 / Service Account

3. GMAIL
   Status: ✅ Connected (stub)
   Actions:
   • send_email — Send emails to clients
   Auth: OAuth2

4. GOOGLE CALENDAR
   Status: ✅ Connected (stub)
   Actions:
   • create_event — Schedule meetings/deadlines
   Auth: OAuth2

USAGE BY AGENTS
---------------
Agents access the Integrator via the shared state:
  integrator = state["integrator"]
  result = integrator.execute("Gemini", "generate_content", {"prompt": "..."})
""",

    "Environment Setup Guide": """
TEMPLO ATELIER — ENVIRONMENT SETUP GUIDE
============================================

PREREQUISITES
-------------
• Python 3.13+
• Node.js (for dashboard frontend)
• Google Cloud Project with enabled APIs

INSTALLATION
------------
1. Clone the repository
2. Create virtual environment:
   python3 -m venv venv
   source venv/bin/activate
3. Install dependencies:
   pip install -r requirements.txt
4. Configure .env file:
   GEMINI_API_KEY=your_key_here
   STUDIO_NAME="Templo Atelier"
   PROJECT_ID=1

RUNNING THE STUDIO
------------------
• Full stack: ./start_studio.sh
• Backend only: uvicorn src.dashboard_api.main:app --reload --port 8000
• Frontend only: cd src/dashboard_ui && npm run dev
• CPO Audit: python3 -m src.meta_core.cpo

API ENDPOINTS
-------------
• Dashboard: http://localhost:3000
• API Docs: http://localhost:8000/docs
• Projects: GET/POST http://localhost:8000/projects/
• Logs: GET/POST http://localhost:8000/logs/
• Interventions: GET http://localhost:8000/interventions/
""",

    # --- 02_Creative_Services ---
    "Brand Strategy Process": """
TEMPLO ATELIER — BRAND STRATEGY PROCESS
==========================================

AGENT: Chief Strategy Agent
TECH: Google Gemini 1.5 Pro
COST: $2.00 per run

INPUT
-----
• Client brief (free-form text)

PROCESS
-------
1. Agent receives client brief from state
2. Constructs structured prompt for Gemini
3. Requests Brand DNA in JSON format
4. Parses response into BrandDNA model

OUTPUT — BRAND DNA
------------------
• name — Brand name
• tagline — Memorable tagline
• mission — Core mission statement
• archetype — Brand archetype (Creator, Ruler, Explorer, etc.)
• core_values — List of 3-5 values
• target_audience — Demographic/psychographic description
• color_palette_hex — 3-5 hex color codes
• typography_primary — Primary font (Google Fonts)
• typography_secondary — Secondary font
• visual_style_prompt — Detailed prompt for image generation

HANDOFF
-------
Brand DNA JSON is stored in state["brand_dna_json"]
→ Visual Stylist uses it for logo/asset generation
→ Social Agent uses it for content tone
→ UI Architect uses it for design system
""",

    "Visual Stylist Process": """
TEMPLO ATELIER — VISUAL STYLIST PROCESS
==========================================

AGENT: Visual Stylist Agent
TECH: Flux Pro (image generation)
COST: $0.50 per image × 4 variants = $2.00

INPUT
-----
• Brand DNA (from Strategist)
• Project budget

PROCESS
-------
1. Check budget via StudioBank
2. If sufficient: Generate 4 logo variants
3. If insufficient: Log ERROR, pause project
4. Generate hero visuals and brand imagery
5. Compile brandbook PDF

OUTPUT
------
• logo_svg_path — Final logo (SVG)
• brand_visuals_paths — Hero images
• brandbook_pdf_path — Complete brand guidelines

BUDGET BEHAVIOR
---------------
• Requires: $2.00 minimum (4 images × $0.50)
• If budget < $2.00: Skips entirely with error log
""",

    "UI/UX Architecture Process": """
TEMPLO ATELIER — UI/UX ARCHITECTURE PROCESS
==============================================

AGENT: UI Architect Agent
TECH: Galileo AI / Figma API
COST: $3.00 per design

INPUT
-----
• Brand DNA (color palette, typography, style)
• Project budget

PROCESS
-------
1. Check budget via StudioBank ($3.00 required)
2. Generate high-fidelity design system in Figma
3. Includes: component library, layouts, responsive views

OUTPUT
------
• figma_design_url — Link to production-ready Figma file

BUDGET BEHAVIOR
---------------
• If budget < $3.00: Returns "SKIPPED_LOW_BUDGET"
""",

    "Social Growth Process": """
TEMPLO ATELIER — SOCIAL GROWTH PROCESS
=========================================

AGENT: Social Growth Agent
TECH: Gemini (text generation, low cost)
COST: ~$0.01 per run (auto-approved)

INPUT
-----
• Brand DNA and visual assets

PROCESS
-------
1. Analyzes brand DNA for tone and messaging
2. Generates monthly content calendar
3. Creates platform-specific posts (Instagram, Twitter, LinkedIn)
4. Includes captions, hashtags, and image prompts

OUTPUT
------
• social_calendar_csv — Monthly content calendar file

NOTE
----
This is a low-cost operation and is usually auto-approved
without CFO intervention.
""",

    "Packaging Design Process": """
TEMPLO ATELIER — PACKAGING DESIGN PROCESS
============================================

AGENT: Packaging Agent
TECH: 3D Rendering Pipeline

INPUT
-----
• Brand visuals (from Stylist)

PROCESS
-------
1. Takes brand visual assets
2. Applies to 3D package templates
3. Renders high-quality mockups

OUTPUT
------
• packaging_files_paths — 3D mockup files (GLB format)
""",

    "Motion Choreography Process": """
TEMPLO ATELIER — MOTION CHOREOGRAPHY PROCESS
================================================

AGENT: Motion Choreographer Agent
TECH: Runway Gen-4 ($15/clip) or Luma Ray 2 ($4/clip)
COST: $4.00-$15.00 per clip

INPUT
-----
• Brand assets and visual style
• Project budget

PROCESS
-------
1. Check budget for premium tier (Runway Gen-4: $15)
2. If sufficient → Render 4K promotional video
3. If insufficient → Check economy tier (Luma Ray 2: $4)
4. If economy available → Render 720p video with warning
5. If no funds → Skip entirely with ERROR

OUTPUT
------
• motion_assets_paths — Video files (MP4)
  Premium: /assets/motion/promo_4k.mp4
  Economy: /assets/motion/promo_720p.mp4

BUDGET TIERS
-------------
  Tier     | Provider     | Quality | Cost
  Premium  | Runway Gen-4 | 4K      | $15.00
  Economy  | Luma Ray 2   | 720p    | $4.00
""",

    # --- 03_Technology ---
    "System Architecture": """
TEMPLO ATELIER — SYSTEM ARCHITECTURE
========================================

OVERVIEW
--------
The system is built as a multi-agent graph using LangGraph.
Agents communicate via a shared state (StudioState).

LAYERS
------

1. OPERATIVE CORE (Business Layer)
   ├── Growth Agent      — Lead acquisition
   ├── CFO Agent         — Budget approval
   ├── Intake Agent      — Client onboarding
   └── Integrator Agent  — API management

2. CREATIVE CORE (Production Layer)
   ├── Strategist        — Brand DNA generation
   ├── Visual Stylist    — Logo & brand assets
   ├── UI Architect      — Figma designs
   ├── Social Growth     — Campaign content
   ├── Packaging         — 3D mockups
   └── Motion            — Video production

3. META CORE (Self-Optimization Layer)
   └── CPO (Chief Process Officer) — Audits & optimization

4. SHARED INFRASTRUCTURE
   ├── StudioState       — TypedDict shared state
   ├── StudioBank        — Budget management
   ├── AgentLogger       — Centralized logging → SQLite
   ├── GoogleDriveService— File I/O
   └── IntegratorAgent   — API gateway

5. DASHBOARD
   ├── Backend           — FastAPI (port 8000)
   └── Frontend          — React/Vite (port 3000)

EXECUTION FLOW
--------------
  Growth → CFO → Strategist → Stylist → [UI, Social, Packaging] → Motion → END
""",

    "Agent Workflow": """
TEMPLO ATELIER — AGENT WORKFLOW (LANGGRAPH PIPELINE)
======================================================

The studio runs as a directed graph using LangGraph's StateGraph.

GRAPH DEFINITION
----------------
  Entry Point: Growth Agent
  
  Growth → CFO
  CFO → Strategist
  Strategist → Stylist
  Stylist → UI/UX (parallel)
  Stylist → Social (parallel)
  Stylist → Packaging (parallel)
  UI/UX → Motion
  Social → Motion
  Packaging → Motion
  Motion → END

SHARED STATE (StudioState)
--------------------------
  project_id: int
  client_brief: str
  project_budget_tokens: float
  project_status: str
  integrator: IntegratorAgent
  brand_dna_json: dict
  logo_svg_path: str
  brand_visuals_paths: list
  brandbook_pdf_path: str
  social_calendar_csv: str
  packaging_files_paths: list
  figma_design_url: str
  motion_assets_paths: list
  feedback_history: list

Each agent reads from and writes to this shared state.
""",

    "Database Schema": """
TEMPLO ATELIER — DATABASE SCHEMA (SQLModel / SQLite)
======================================================

DATABASE: studio.db (SQLite)

TABLE: project
--------------
  id              INTEGER PRIMARY KEY
  name            TEXT
  status          TEXT DEFAULT 'Intake'
  client_brief    TEXT
  budget_cap      FLOAT
  budget_spent    FLOAT DEFAULT 0.0
  created_at      DATETIME

TABLE: agentlog
---------------
  id              INTEGER PRIMARY KEY
  project_id      INTEGER FK → project.id
  agent_name      TEXT
  message         TEXT
  severity        TEXT DEFAULT 'INFO' (INFO/WARN/ERROR)
  cost_incurred   FLOAT DEFAULT 0.0
  timestamp       DATETIME

TABLE: interventionrequest
--------------------------
  id                INTEGER PRIMARY KEY
  project_id        INTEGER FK → project.id
  requesting_agent  TEXT
  description       TEXT
  cost_implication  FLOAT
  status            TEXT DEFAULT 'PENDING' (PENDING/APPROVED/DENIED)
  timestamp         DATETIME
""",

    "Deployment & Running Guide": """
TEMPLO ATELIER — DEPLOYMENT & RUNNING GUIDE
==============================================

QUICK START
-----------
  ./start_studio.sh

This launches:
  1. Backend API on port 8000 (uvicorn + FastAPI)
  2. Frontend UI on port 3000 (Vite + React)

INDIVIDUAL COMMANDS
-------------------
  # Activate environment
  source venv/bin/activate

  # Backend only
  uvicorn src.dashboard_api.main:app --reload --port 8000

  # Frontend only
  cd src/dashboard_ui && npm run dev

  # Run full studio workflow
  python3 -m src.studio

  # Run CPO Audit
  python3 -m src.meta_core.cpo

  # Run Intake Agent
  python3 -m src.operative_core.intake

ENVIRONMENT VARIABLES
---------------------
  GEMINI_API_KEY  — Required for AI generation
  STUDIO_NAME     — Studio name (Templo Atelier)
  PROJECT_ID      — Default project ID
""",

    # --- 04_Quality ---
    "CPO Audit Process": """
TEMPLO ATELIER — CPO AUDIT PROCESS
=====================================

AGENT: Chief Process Officer (CPO)
ROLE: Meta-agent that audits the entire studio

AUDIT TYPES
-----------

1. PERFORMANCE AUDIT
   • Queries AgentLog table in SQLite
   • Calculates error rate (errors / total logs × 100)
   • Flags if error rate > 10%
   • Reports total API spend across all agents

2. TASK COMPLETION AUDIT
   • Reads task.md checklist
   • Identifies pending (unchecked) tasks
   • Cross-references with file system
   • Detects "implemented but unchecked" discrepancies

ALERTS
------
  > 10% error rate → "Review Agent Prompts"
  Pending tasks found → Lists top 5 uncompleted items
  Code exists but task unchecked → "INSIGHT" notification

RUNNING
-------
  python3 -m src.meta_core.cpo
""",

    # --- 05_Projects ---
    "Project Template": """
TEMPLO ATELIER — PROJECT TEMPLATE
====================================

Every new client project follows this folder structure:

  /projects/{Year}/{Project_Name}/
  │
  ├── 00_Intake/
  │   └── Initial_Proposal.md
  │
  ├── 01_Strategy/
  │   └── Brand_DNA.json
  │
  ├── 02_Design/
  │   ├── logos/
  │   ├── visuals/
  │   ├── brandbook.pdf
  │   └── figma_link.txt
  │
  ├── 03_Finance/
  │   └── budget_report.csv
  │
  ├── 99_Delivery/
  │   └── (final packaged assets)
  │
  └── .antigravity/
      └── mission (YAML mission file)

MISSION FILE FORMAT (YAML)
--------------------------
  name: "Launch ProjectName"
  status: "In Progress"
  completion: 0.20
  active_agents: [strategist, stylist, cfo]
  next_step: "Review Initial Proposal"
  context:
    project_name: "ProjectName"
    client_goals: [...]
    deliverables: [...]
    hard_deadlines: {}
    budget_hint: null
""",
}

# ============================================================
# FOLDER STRUCTURE DEFINITION
# ============================================================

STRUCTURE = {
    "Templo Atelier": {
        "00_Company": {
            "_docs": ["Company Overview", "Mission & Vision", "Service Catalog", "Pricing & Cost Structure"]
        },
        "01_Operations": {
            "Intake": {
                "_docs": ["Intake Process", "Client Onboarding Checklist"]
            },
            "Finance": {
                "_docs": ["Budget Management", "API Cost Table"]
            },
            "Growth": {
                "_docs": ["Lead Generation Process"]
            },
            "Integrations": {
                "_docs": ["API Registry", "Environment Setup Guide"]
            }
        },
        "02_Creative_Services": {
            "Strategy": {
                "_docs": ["Brand Strategy Process"]
            },
            "Visual_Identity": {
                "_docs": ["Visual Stylist Process"]
            },
            "UI_UX_Design": {
                "_docs": ["UI/UX Architecture Process"]
            },
            "Social_Media": {
                "_docs": ["Social Growth Process"]
            },
            "Packaging": {
                "_docs": ["Packaging Design Process"]
            },
            "Motion_Graphics": {
                "_docs": ["Motion Choreography Process"]
            }
        },
        "03_Technology": {
            "_docs": ["System Architecture", "Agent Workflow", "Database Schema", "Deployment & Running Guide"]
        },
        "04_Quality": {
            "_docs": ["CPO Audit Process"]
        },
        "05_Projects": {
            "_docs": ["Project Template"]
        }
    }
}


def build_structure(drive, docs, tree: dict, parent_id: Optional[str] = None):
    """Recursively creates folders and docs from the structure definition."""
    for name, children in tree.items():
        folder_id = find_or_create_folder(drive, name, parent_id)

        if isinstance(children, dict):
            # Create docs if defined
            doc_list = children.pop("_docs", [])
            for doc_title in doc_list:
                content = DOCS.get(doc_title, f"[Content pending for: {doc_title}]")
                create_google_doc(drive, docs, doc_title, folder_id, content)

            # Recurse into subfolders
            if children:
                build_structure(drive, docs, children, folder_id)


def main():
    print("\n🏛️  TEMPLO ATELIER — Google Drive Documentation Generator\n")
    print("=" * 55)

    # 1. Authenticate
    print("\n1. Authenticating with Google...")
    creds = authenticate()
    print("   ✅ Authenticated successfully\n")

    # 2. Build services
    drive, docs = get_services(creds)

    # 3. Create structure
    print("2. Creating folder structure and documents...\n")
    build_structure(drive, docs, STRUCTURE)

    print("\n" + "=" * 55)
    print("✅ DONE! Check your Google Drive for 'Templo Atelier' folder.")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
