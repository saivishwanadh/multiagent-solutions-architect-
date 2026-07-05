from src.schemas.state import SupervisorState
from langgraph.types import interrupt
from src.config.settings import get_llm
from pydantic import BaseModel, Field

class ExtractedConstraints(BaseModel):
    budget: float | None = Field(description="The numeric budget in USD if provided.")
    timeline_weeks: int | None = Field(description="The numeric timeline in weeks if provided.")

async def node_clarification(state: SupervisorState) -> SupervisorState:
    vi = state.get("persistent_context", {}).get("business_constraints")
    if vi:
        critical_missing = [m for m in vi.missing_info if "budget" in m.lower() or "timeline" in m.lower()]
        if critical_missing and vi.query_category in (1, 3):
            user_response = interrupt({
                "message": "I need a few more details before proceeding:",
                "missing": critical_missing
            })
            
            if user_response and isinstance(user_response, str):
                llm = get_llm(temperature=0.0).with_structured_output(ExtractedConstraints)
                extracted = await llm.ainvoke(f"Extract budget and timeline from this user response: '{user_response}'")
                
                if extracted.budget and vi.constraints:
                    vi.constraints.budget = extracted.budget
                elif extracted.budget:
                    from src.schemas.validated_input import ExplicitConstraints
                    vi.constraints = ExplicitConstraints(budget=extracted.budget, timeline_weeks=None)
                    
                if extracted.timeline_weeks and vi.constraints:
                    vi.constraints.timeline_weeks = extracted.timeline_weeks
                    
            vi.missing_info = [m for m in vi.missing_info if m not in critical_missing]
            return {"persistent_context": {"business_constraints": vi}}
            
    return {}
