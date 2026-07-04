from pydantic import BaseModel, Field
from src.config.settings import get_llm
from src.schemas.state import SupervisorState
from langgraph.types import interrupt

class DeadlockOption(BaseModel):
    description: str = Field(description="A clear, concise description of the option. E.g. 'Increase budget to $20k to keep current scope.'")
    adjusted_budget: float | None = Field(description="The new suggested budget, if applicable.")
    adjusted_timeline_weeks: int | None = Field(description="The new suggested timeline in weeks, if applicable.")
    scope_reduction: bool = Field(description="Whether this option requires significantly cutting scope.")
    architecture_change: bool = Field(description="Whether this option requires changing the architecture or tech stack.")

class DeadlockOptions(BaseModel):
    options: list[DeadlockOption] = Field(description="A list of 2-3 viable options for the user.")

def generate_deadlock_options(state: SupervisorState) -> list[dict]:
    """Uses LLM to generate 2-3 valid options based on failed attempts."""
    
    ce = state.get("cost_estimate")
    ra = state.get("risk_assessment")
    vi = state.get("validated_input")
    history = state.get("negotiation_history", [])
    
    prompt = f"""
    The multi-agent system has failed to find a valid project blueprint after max negotiation iterations.
    
    Original Constraints:
    - Budget: ${vi.constraints.budget if vi and vi.constraints else 'None'}
    - Timeline: {vi.constraints.timeline_weeks if vi and vi.constraints else 'None'} weeks
    
    Current State:
    - Estimated Cost: ${ce.total_estimated_cost if ce else 0}
    - Risk Level / Feasibility: {ra.feasibility_verdict if ra else 'Unknown'}
    
    Negotiation History Summary:
    {history}
    
    Generate 2-3 realistic options for the user to proceed.
    Examples:
    - Increase budget to match the estimated cost.
    - Keep budget but drastically reduce scope.
    - Extend timeline and switch to cheaper technology.
    """
    
    llm = get_llm(temperature=0.3)
    structured_llm = llm.with_structured_output(DeadlockOptions)
    result = structured_llm.invoke(prompt)
    
    return [opt.model_dump() for opt in result.options]

async def node_invoke_hitl(state: SupervisorState) -> dict:
    if not state.get("deadlock_options"):
        options = generate_deadlock_options(state)
        # We must return to set deadlock_options in state, then interrupt.
        # But langgraph interrupt is cleaner if we do it immediately if options exist.
        # We will yield state updates directly
        pass # Actually langgraph handles this differently, let's just do it inline
    else:
        options = state["deadlock_options"]
        
    if not state.get("deadlock_options"):
        options = generate_deadlock_options(state)
        state["deadlock_options"] = options
        
    user_choice = interrupt({
        "message": "Could not meet constraints after max attempts.",
        "options": options
    })
    
    updates = {"user_choice": user_choice}
    
    if user_choice and options:
        idx = ord(user_choice.upper()) - 65
        if 0 <= idx < len(options):
            selected = options[idx]
            vi = state.get("validated_input")
            if vi and getattr(vi, "constraints", None):
                if selected.get("adjusted_budget"):
                    vi.constraints.budget = selected["adjusted_budget"]
                if selected.get("adjusted_timeline_weeks"):
                    vi.constraints.timeline_weeks = selected["adjusted_timeline_weeks"]
            updates["validated_input"] = vi
            
            if selected.get("scope_reduction"):
                from src.schemas.conflict_feedback import ConflictFeedback, ViolatedConstraint
                updates["conflict_feedback"] = ConflictFeedback(
                    iteration_number=state.get("conflict_loop_count", 0),
                    violated_constraints=[
                        ViolatedConstraint(
                            constraint_type="budget", 
                            target_value="User Budget",
                            current_value="Too High"
                        )
                    ],
                    guidance="User explicitly requested scope reduction to meet constraints during HITL deadlock.",
                    optimization_target="scope",
                    previous_trims=[]
                )
            
    # Reset conflict loop and options so we can try again
    updates["conflict_loop_count"] = 0
    updates["total_hitl_count"] = state.get("total_hitl_count", 0) + 1
    updates["deadlock_options"] = None
    return updates
