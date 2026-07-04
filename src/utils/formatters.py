from src.schemas.validated_input import ExplicitConstraints

def format_features(features: list) -> str:
    """Compresses a list of Feature models into a dense markdown string."""
    if not features:
        return "None"
    
    parts = []
    for f in features:
        priority = getattr(f, 'priority', 'Medium')
        complexity = getattr(f, 'complexity', 'Medium')
        category = getattr(f, 'category', 'General')
        desc = getattr(f, 'description', '')
        
        parts.append(f"- {f.name} [Pri: {priority} | Cplx: {complexity} | Cat: {category}]: {desc}")
        
    return "\n".join(parts)

def format_constraints(constraints: ExplicitConstraints) -> str:
    """Compresses ExplicitConstraints into a dense string, dropping None values."""
    if not constraints:
        return "None"
        
    parts = []
    if constraints.budget: parts.append(f"Budget: ${constraints.budget:,.0f}")
    if constraints.timeline_weeks: parts.append(f"Timeline: {constraints.timeline_weeks}w")
    if constraints.deployment_model: parts.append(f"Deployment: {constraints.deployment_model}")
    if constraints.team_size: parts.append(f"Team Size: {constraints.team_size}")
    if constraints.industry: parts.append(f"Industry: {constraints.industry}")
    
    if constraints.tech_preferences: parts.append(f"Tech: {', '.join(constraints.tech_preferences)}")
    if constraints.compliance_needs: parts.append(f"Compliance: {', '.join(constraints.compliance_needs)}")
    
    return " | ".join(parts) if parts else "No explicit constraints."

def format_risks(risks: list) -> str:
    """Compresses Risk models into dense strings."""
    if not risks:
        return "None"
        
    parts = []
    for r in risks:
        sev = getattr(r, 'severity', 'medium').upper()
        desc = getattr(r, 'description', '')
        mit = getattr(r, 'mitigation', '')
        parts.append(f"- [{sev}] {desc} (Mitigation: {mit})")
        
    return "\n".join(parts)
