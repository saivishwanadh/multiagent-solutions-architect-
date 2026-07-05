from src.config.settings import get_llm
from src.agents.scope.state import ScopeState, FeatureList
from src.agents.scope.utils import read_scope_prompt

async def node_feature_extractor(state: ScopeState) -> dict:
    llm = get_llm(temperature=0.0).with_structured_output(FeatureList)
    sys_prompt = read_scope_prompt("feature_extractor.txt")
    
    content = f"Parsed Requirements:\n{state['parsed_requirements']}\n"
    
    if state.get("conflict_feedback") and state["conflict_feedback"].optimization_target in ("scope", "both"):
        content += "\nWARNING: Project is over budget. Only extract absolutely essential P0/P1 features. Drop P2/P3 nice-to-haves."
        
    if state.get("coverage_feedback"):
        content += f"\n{state['coverage_feedback']}\n"
        
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": content}
    ]
    
    feature_data = await llm.ainvoke(messages)
    return {"features": feature_data.features}
