from src.config.settings import get_llm
from src.agents.risk.state import RiskState, RiskList
from src.agents.risk.utils import read_risk_prompt, get_relevant_lessons

async def node_timeline_validator(state: RiskState) -> dict:
    llm = get_llm(temperature=0.0).with_structured_output(RiskList)
    sys_prompt = read_risk_prompt("timeline_validator.txt")
    
    features_subset = [{"name": f.name, "category": f.category} for f in state['project_blueprint'].features]
    content = f"Features:\n{features_subset}\n"
    
    vi = state.get("validated_input")
    user_timeline = vi.constraints.timeline_weeks if vi and vi.constraints and vi.constraints.timeline_weeks else sum(m.duration_weeks for m in state["project_blueprint"].milestones)
    
    content += f"Estimated Timeline: {user_timeline} weeks\n"
    
    relevant_lessons = get_relevant_lessons(state, ["timeline", "delay", "schedule"])
    if relevant_lessons:
        content += f"Historical Lessons:\n{relevant_lessons}\n"
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": content}
    ]
    result = await llm.ainvoke(messages)
    return {"timeline_risks": result.risks}
