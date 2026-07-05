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
    
    ce = state.get("working_outputs", {}).get("cost_estimate")
    ra = state.get("working_outputs", {}).get("risk_assessment")
    vi = state.get("persistent_context", {}).get("business_constraints")
    history = state.get("persistent_context", {}).get("negotiation_history", [])
    
    prompt = f"""
    The multi-agent system has failed to find a valid project blueprint after max negotiation iterations.
    
    Original Constraints:
    - Budget: ${vi.constraints.budget if vi and getattr(vi, 'constraints', None) else 'None'}
    - Timeline: {vi.constraints.timeline_weeks if vi and getattr(vi, 'constraints', None) else 'None'} weeks
    
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
    options = state.get("runtime_state", {}).get("deadlock_options")
        
    if not options:
        options = generate_deadlock_options(state)
        # We can yield state updates directly in LangGraph if needed, but we'll do it synchronously here
        
    user_choice = interrupt({
        "message": "Could not meet constraints after max attempts.",
        "options": options
    })
    
    rs_updates = {"user_choice": user_choice}
    pc_updates = {}
    
    if user_choice and options:
        idx = ord(user_choice.upper()) - 65
        if 0 <= idx < len(options):
            selected = options[idx]
            vi = state.get("persistent_context", {}).get("business_constraints")
            if vi and getattr(vi, "constraints", None):
                if selected.get("adjusted_budget"):
                    vi.constraints.budget = selected["adjusted_budget"]
                if selected.get("adjusted_timeline_weeks"):
                    vi.constraints.timeline_weeks = selected["adjusted_timeline_weeks"]
            pc_updates["business_constraints"] = vi
            
            if selected.get("scope_reduction"):
                from src.schemas.conflict_feedback import ConflictFeedback, ViolatedConstraint
                rs_updates["conflict_feedback"] = ConflictFeedback(
                    iteration_number=state.get("runtime_state", {}).get("conflict_loop_count", 0),
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
    rs_updates["conflict_loop_count"] = 0
    pc_updates["total_hitl_count"] = state.get("persistent_context", {}).get("total_hitl_count", 0) + 1
    rs_updates["deadlock_options"] = None
    
    return {
        "runtime_state": rs_updates,
        "persistent_context": pc_updates
    }
