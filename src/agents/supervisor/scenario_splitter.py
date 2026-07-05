import os
from pydantic import BaseModel, Field
from src.config.settings import get_llm
from src.schemas.state import SupervisorState

class SplitScenarios(BaseModel):
    scenario_a_prompt: str = Field(description="Complete prompt for the first scenario.")
    scenario_b_prompt: str = Field(description="Complete prompt for the second scenario.")

async def split_scenarios(user_prompt: str) -> SplitScenarios:
    path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "prompts", "scenario_splitter.txt")
    with open(path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
        
    llm = get_llm(temperature=0.1)
    structured_llm = llm.with_structured_output(SplitScenarios)
    return await structured_llm.ainvoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])

async def node_scenario_splitter(state: SupervisorState) -> dict:
    import asyncio
    from src.agents.supervisor.tradeoff_pipeline import run_pipeline_for_scenario
    
    prompt = state.get("persistent_context", {}).get("latest_user_prompt", "")
    split_result = await split_scenarios(prompt)
    lessons = state.get("persistent_context", {}).get("org_lessons", [])
    
    # Run scenarios simultaneously using asyncio.gather
    res_a, res_b = await asyncio.gather(
        run_pipeline_for_scenario(split_result.scenario_a_prompt, lessons),
        run_pipeline_for_scenario(split_result.scenario_b_prompt, lessons)
    )
    
    return {
        "runtime_state": {
            "scenario_a_result": res_a,
            "scenario_b_result": res_b
        }
    }
