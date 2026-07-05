from src.schemas.state import SupervisorState

def route_by_category(state: SupervisorState) -> str:
    """Routes to different pipeline paths based on query category."""
    vi = state.get("persistent_context", {}).get("business_constraints")
    
    if not vi:
        return "reject"
        
    is_valid = getattr(vi, "is_valid", vi.get("is_valid") if isinstance(vi, dict) else False)
    if not is_valid:
        return "reject"
    
    category = getattr(vi, "query_category", vi.get("query_category") if isinstance(vi, dict) else 1)
    
    if category == 1:    
        return "full_pipeline"         # Scope -> Arch -> Finance -> Risk
    elif category == 2:  
        return "full_pipeline"         # Route architecture queries through Scope first to guarantee features
    elif category == 3:  
        return "full_pipeline"         # Same as Cat 1
    elif category == 4:  
        return "tradeoff"              # Placeholder for Phase 13
    elif category == 5:  
        return "pivot"                 # Placeholder for Phase 13
    elif category == 6:
        return "direct_qa"             # Fast path for follow-up questions
        
    return "full_pipeline"
