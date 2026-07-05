from src.config.settings import get_llm
from src.agents.scope.state import ScopeState
from src.agents.scope.utils import read_scope_prompt

async def node_requirement_parser(state: ScopeState) -> dict:
    llm = get_llm(temperature=0.0)
    sys_prompt = read_scope_prompt("requirement_parser.txt")
    
    content = f"Initial Business Objective: {state.get('initial_user_prompt')}\n"
    if state.get("latest_user_prompt") and state.get("latest_user_prompt") != state.get("initial_user_prompt"):
        content += f"Latest Modification Request: {state.get('latest_user_prompt')}\n"
        
    content += f"\nAnalyzed Project Summary: {state['validated_input'].project_summary}\n"
    content += f"Extracted Constraints: {state['validated_input'].constraints.model_dump_json()}\n"
    
    if state.get("conflict_feedback"):
        cf = state["conflict_feedback"]
        content += f"\n\nCRITICAL CONFLICT FEEDBACK (Iteration {cf.iteration_number}):\n"
        content += f"Guidance: {cf.guidance}\n"
        for vc in cf.violated_constraints:
            content += f"  - Violated: {vc.constraint_type} (target={vc.target_value}, current={vc.current_value})\n"
        if cf.optimization_target in ("scope", "both"):
            content += "You MUST extract fewer, leaner requirements to drastically reduce costs.\n"
            
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": content}
    ]
    
    response = await llm.ainvoke(messages)
    return {"parsed_requirements": response.content}
