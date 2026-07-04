from src.schemas.state import SupervisorState
from src.schemas.conflict_feedback import ViolatedConstraint, ConflictFeedback

def check_conflicts(state: SupervisorState) -> str:
    """Returns: 'pass', 'conflict', or 'deadlock'."""
    ce = state.get("cost_estimate")
    ra = state.get("risk_assessment")
    
    budget_ok = (ce.budget_verdict == "PASS") if ce else True
    feasible = (ra.feasibility_verdict in ("FEASIBLE", "RISKY")) if ra else True
    
    if budget_ok and feasible:
        return "pass"
    
    if state.get("total_hitl_count", 0) >= 2:
        return "pass"
    
    max_loops = 1 if state.get("total_hitl_count", 0) > 0 else 3
    
    if state.get("conflict_loop_count", 0) < max_loops:
        return "conflict"
    else:
        return "deadlock"

def generate_conflict_feedback(state: SupervisorState) -> SupervisorState:
    """Creates ConflictFeedback from cost/risk data."""
    ce = state.get("cost_estimate")
    ra = state.get("risk_assessment")
    
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
    for entry in state.get("negotiation_history", []):
        prev_trims.extend(entry.get("trimmed_features", []))
        
    # Also extract anything that was trimmed just now.
    # The blueprint synthesizer or scope sub-graph hasn't run yet, but we'll track the differences later.
    
    # Get highest cost features
    highest = []
    if ce and ce.cost_per_feature:
        highest = sorted(ce.cost_per_feature, key=lambda x: x.estimated_cost, reverse=True)[:5]
    
    state["conflict_loop_count"] = state.get("conflict_loop_count", 0) + 1
    loop_count = state["conflict_loop_count"]
    if loop_count == 1:
        guidance = "Iteration 1/3: Focus on reducing infrastructure costs. Consider smaller GPUs, cheaper hosting, or open-source alternatives."
    elif loop_count == 2:
        guidance = "Iteration 2/3: Focus on reducing scope. Move P2 and P3 features to later phases or remove them entirely."
    else:
        guidance = "Iteration 3/3: Aggressive reduction needed. Cut any non-P0 features and aggressively downgrade infrastructure."
        
    state["conflict_feedback"] = ConflictFeedback(
        violated_constraints=violated,
        highest_cost_features=highest,
        iteration_number=loop_count,
        previous_trims=prev_trims,
        guidance=guidance,
        optimization_target=state.get("refinement_target", "scope")
    )
    
    # Record in negotiation_history
    state["negotiation_history"].append({
        "iteration": state["conflict_loop_count"],
        "violated": [v.constraint_type for v in violated],
        "trimmed_features": prev_trims,
        "total_cost": ce.total_estimated_cost if ce else 0,
        "risk_level": ra.overall_risk_level if ra else "UNKNOWN"
    })
    
    return state
