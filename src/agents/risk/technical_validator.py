from src.config.settings import get_llm
from src.agents.risk.state import RiskState, RiskList
from src.agents.risk.utils import read_risk_prompt, get_relevant_lessons

async def node_technical_validator(state: RiskState) -> dict:
    llm = get_llm(temperature=0.0).with_structured_output(RiskList)
    sys_prompt = read_risk_prompt("technical_validator.txt")
    
    content = f"Architecture Tech Stack:\n{state['project_blueprint'].tech_stack.model_dump_json()}\n"
    if state["project_blueprint"].architecture_pattern:
        content += f"Pattern: {state['project_blueprint'].architecture_pattern.name}\n"
    
    relevant_lessons = get_relevant_lessons(state, ["architecture", "infrastructure", "database", "integration"])
    if relevant_lessons:
        content += f"Historical Lessons:\n{relevant_lessons}\n"
        
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": content}
    ]
    result = await llm.ainvoke(messages)
    return {"technical_risks": result.risks}
