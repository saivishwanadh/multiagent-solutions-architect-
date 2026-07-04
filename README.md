# Multi-Agent Orchestration

**Autonomous Solutions Architect & Estimator** — A production-grade enterprise agent that ingests project prompts, evaluates them against technical and financial constraints, and produces finalized project blueprints.

Built with [LangGraph](https://langchain-ai.github.io/langgraph/) + Google Gemini.

---

## Quick Start

### 1. Clone and create virtual environment

```bash
git clone <repo-url>
cd multi-agent-orchestration
python -m venv venv
```

### 2. Activate the virtual environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Copy `.env.example` to `.env` and add your Google Gemini API key:

```bash
cp .env.example .env
# Edit .env and replace your-api-key-here with your actual key
```

### 5. Run

```bash
python main.py
```

---

## Project Structure

```
multi-agent-orchestration/
├── src/
│   ├── agents/          # Agent logic (Blueprint Synthesizer, Guardrails)
│   ├── config/          # Settings and Prompts
│   ├── graphs/          # LangGraph Sub-graphs (Scope, Architecture, Finance, Risk, Supervisor)
│   ├── knowledge_base/  # Organizational lessons and knowledge
│   ├── routing/         # Routers, Conflict Loops, Tradeoff Handlers
│   └── schemas/         # Pydantic state models and structured outputs
├── main.py              # CLI Entry point
├── requirements.txt
├── .env                 # API keys (not committed)
├── .env.example         # Template for .env
├── .gitignore
└── README.md
```

---

## Current Status: Advanced Prototype / Beta

The system features an advanced hierarchical multi-agent architecture built on **LangGraph**. It utilizes a Supervisor graph that orchestrates specialized sub-graphs (Scope, Architecture, Finance, Risk) with state passing and checkpointers. It includes:
- **Intake Guardrails** for request categorization (Feasibility, Architecture, Budget, Trade-offs).
- **Automated Conflict Resolution** (auto-trimming features if over budget).
- **Human-In-The-Loop (HITL)** for breaking deadlocks when constraints cannot be met automatically.
- **Trade-off Analysis** for comparing parallel architecture scenarios.
