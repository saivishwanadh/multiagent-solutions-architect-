import os
from src.agents.risk.state import RiskState
from src.memory.vector_store import get_lessons

def read_risk_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "prompts", "risk", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_relevant_lessons(state: RiskState, extra_keywords: list[str] = None) -> list[str]:
    keywords = set(extra_keywords or [])
    if state.get("project_blueprint"):
        for f in state["project_blueprint"].features:
            keywords.add(f.category.lower())
            
        stack = state["project_blueprint"].tech_stack
        if stack:
            for val in [stack.frontend, stack.backend, stack.database, stack.infrastructure]:
                if val:
                    keywords.add(str(val).lower())
                
    query = " ".join(list(keywords)[:5]) # Top 5 keywords for semantic search
    return get_lessons(query, k=3)
