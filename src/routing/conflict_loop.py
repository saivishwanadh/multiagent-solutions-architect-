from src.schemas.state import SupervisorState
from src.schemas.conflict_feedback import ViolatedConstraint, ConflictFeedback

def check_conflicts(state: SupervisorState) -> str:
    """Returns: 'pass', 'conflict', or 'deadlock'."""
    ce = state.get("working_outputs", {}).get("cost_estimate")
    ra = state.get("working_outputs", {}).get("risk_assessment")
    
    budget_ok = (ce.budget_verdict == "PASS") if ce else True
    feasible = (ra.feasibility_verdict in ("FEASIBLE", "RISKY")) if ra else True
    
    if budget_ok and feasible:
        return "pass"
    
    total_hitl_count = state.get("persistent_context", {}).get("total_hitl_count", 0)
    if total_hitl_count >= 2:
        return "pass"
    
    max_loops = 1 if total_hitl_count > 0 else 3
    conflict_loop_count = state.get("runtime_state", {}).get("conflict_loop_count", 0)
    
    if conflict_loop_count < max_loops:
        return "conflict"
    else:
        return "deadlock"

def generate_conflict_feedback(state: SupervisorState) -> dict:
    """Creates ConflictFeedback from cost/risk data."""
    ce = state.get("working_outputs", {}).get("cost_estimate")
    ra = state.get("working_outputs", {}).get("risk_assessment")
    
    violated = []
    if ce and ce.budget_verdict == "OVER_BUDGET":
        violated.append(ViolatedConstraint(
            constraint_type="budget",
            target_value=ce.user_budget or 0,
            current_value=ce.total_estimated_cost,
            overshoot=ce.budget_delta
        ))
    if ra and ra.feasibility_verdict == "INFEASIBLE":
        violated.append(ViolatedConstraint(
            constraint_type="technical_feasibility",
            target_value="FEASIBLE",
            current_value=ra.feasibility_verdict,
            overshoot=None
        ))
    
    # Extract previously trimmed features from negotiation_history
    prev_trims = []
    for entry in state.get("persistent_context", {}).get("negotiation_history", []):
        prev_trims.extend(entry.get("trimmed_features", []))
        
    # Get highest cost features
    highest = []
    if ce and ce.cost_per_feature:
        highest = sorted(ce.cost_per_feature, key=lambda x: x.estimated_cost, reverse=True)[:5]
    
    current_loop_count = state.get("runtime_state", {}).get("conflict_loop_count", 0) + 1
    
    if current_loop_count == 1:
        guidance = "Iteration 1/3: Focus on reducing infrastructure costs. Consider smaller GPUs, cheaper hosting, or open-source alternatives."
    elif current_loop_count == 2:
        guidance = "Iteration 2/3: Focus on reducing scope. Move P2 and P3 features to later phases or remove them entirely."
    else:
        guidance = "Iteration 3/3: Aggressive reduction needed. Cut any non-P0 features and aggressively downgrade infrastructure."
        
    conflict_feedback = ConflictFeedback(
        violated_constraints=violated,
        highest_cost_features=highest,
        iteration_number=current_loop_count,
        previous_trims=prev_trims,
        guidance=guidance,
        optimization_target=state.get("runtime_state", {}).get("refinement_target") or "scope"
    )
    
    # Record in negotiation_history
    new_history_entry = {
        "iteration": current_loop_count,
        "violated": [v.constraint_type for v in violated],
        "trimmed_features": prev_trims,
        "total_cost": ce.total_estimated_cost if ce else 0,
        "risk_level": ra.overall_risk_level if ra else "UNKNOWN"
    }
    
    history = state.get("persistent_context", {}).get("negotiation_history", [])
    history.append(new_history_entry)
    
    return {
        "runtime_state": {
            "conflict_loop_count": current_loop_count,
            "conflict_feedback": conflict_feedback
        },
        "persistent_context": {
            "negotiation_history": history
        }
    }
