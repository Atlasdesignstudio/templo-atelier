# 1-Person AI Creative Studio (2026 Edition)

## Setup
1.  **Create Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Environment Variables**:
    Create a `.env` file with your API keys:
    ```bash
    OPENAI_API_KEY=sk-...
    RUNWAY_API_KEY=...
    ```

## Usage

### 1. Run the Studio (Simulation)
Executes the full "Concept to Handoff" workflow for a sample brief.
```bash
python3 -m src.studio
```

### 2. Run the Glass House Dashboard
Starts the FastAPI backend.
```bash
uvicorn src.dashboard_api.main:app --reload
```

### 3. Run the CPO Audit
Checks logs and optimizes the system.
```bash
python3 -m src.meta_core.cpo
```

## Architecture
*   `src/operative_core`: Business logic (CFO, Growth).
*   `src/creative_core`: Production logic (Strategy, Design, Motion).
*   `src/meta_core`: Self-optimization (CPO).
*   `src/dashboard_api`: Observability backend.
