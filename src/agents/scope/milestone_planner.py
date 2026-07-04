from src.config.settings import get_llm
from src.agents.scope.state import ScopeState, MilestoneList
from src.agents.scope.utils import read_scope_prompt
from src.utils.formatters import format_features, format_constraints

async def node_milestone_planner(state: ScopeState) -> dict:
    llm = get_llm(temperature=0.0).with_structured_output(MilestoneList)
    sys_prompt = read_scope_prompt("milestone_planner.txt")
    
    features_text = format_features(state.get("features") or [])
    constraints_text = format_constraints(state['validated_input'].constraints)
    
    content = f"Constraints: {constraints_text}\n"
    content += f"Features to Group:\n{features_text}"
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": content}
    ]
    
    milestone_data = await llm.ainvoke(messages)
    return {"milestones": milestone_data.milestones}
