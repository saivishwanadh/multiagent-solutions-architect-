from src.config.settings import get_llm
from src.agents.risk.state import RiskState, RiskList
from src.agents.risk.utils import read_risk_prompt, get_relevant_lessons

async def node_security_validator(state: RiskState) -> dict:
    llm = get_llm(temperature=0.0).with_structured_output(RiskList)
    sys_prompt = read_risk_prompt("security_validator.txt")
    
    content = f"Architecture Tech Stack:\n{state['project_blueprint'].tech_stack.model_dump_json()}\n"
    features_subset = [{"name": f.name, "category": f.category} for f in state['project_blueprint'].features]
    content += f"Features (for context on data handled):\n{features_subset}\n"
    
    relevant_lessons = get_relevant_lessons(state, ["security", "compliance", "privacy", "data", "pii", "phi"])
    if relevant_lessons:
        content += f"Historical Lessons:\n{relevant_lessons}\n"
        
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": content}
    ]
    result = await llm.ainvoke(messages)
    return {"security_risks": result.risks}
