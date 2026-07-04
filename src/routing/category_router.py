from src.schemas.state import SupervisorState

def route_by_category(state: SupervisorState) -> str:
    """Routes to different pipeline paths based on query category."""
    vi = state.get("validated_input")
    if not vi or not vi.is_valid:
        return "reject"
    
    category = vi.query_category
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
