import os
from src.config.settings import get_llm
from src.schemas.state import SupervisorState
from src.schemas.scenario_comparison import ScenarioComparison

async def compare_scenarios(scenario_a_result: dict, scenario_b_result: dict) -> ScenarioComparison:
    path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "prompts", "scenario_comparator.txt")
    with open(path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
        
    prompt = f"""
    Compare these two scenarios:
    
    SCENARIO A:
    Cost: ${scenario_a_result.get('cost_estimate').total_estimated_cost if scenario_a_result.get('cost_estimate') else 0}
    Risk: {scenario_a_result.get('risk_assessment').overall_risk_level if scenario_a_result.get('risk_assessment') else 'UNKNOWN'}
    Architecture: {scenario_a_result.get('project_blueprint').tech_stack.backend if scenario_a_result.get('project_blueprint') and scenario_a_result.get('project_blueprint').tech_stack else 'UNKNOWN'}
    
    SCENARIO B:
    Cost: ${scenario_b_result.get('cost_estimate').total_estimated_cost if scenario_b_result.get('cost_estimate') else 0}
    Risk: {scenario_b_result.get('risk_assessment').overall_risk_level if scenario_b_result.get('risk_assessment') else 'UNKNOWN'}
    Architecture: {scenario_b_result.get('project_blueprint').tech_stack.backend if scenario_b_result.get('project_blueprint') and scenario_b_result.get('project_blueprint').tech_stack else 'UNKNOWN'}
    """
    
    llm = get_llm(temperature=0.3)
    structured_llm = llm.with_structured_output(ScenarioComparison)
    return await structured_llm.ainvoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ])

async def node_scenario_comparator(state: SupervisorState) -> dict:
    res_a = state.get("scenario_a_result")
    res_b = state.get("scenario_b_result")
    if res_a and res_b:
        comparison = await compare_scenarios(res_a, res_b)
        return {"scenario_comparison": comparison}
    return {}
