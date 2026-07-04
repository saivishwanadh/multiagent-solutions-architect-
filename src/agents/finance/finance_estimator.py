from src.config.settings import get_llm
from src.schemas.cost_estimate import CostEstimate
from src.agents.finance.state import FinanceState

async def node_finance_estimator(state: FinanceState) -> dict:
    """Generates the final CostEstimate using data gathered by the researcher."""
    llm = get_llm(temperature=0.0).with_structured_output(CostEstimate)
    
    sys_prompt = (
        "You are the Finance Estimator. Review the tool outputs from the Finance Researcher.\n"
        "Compile all development, infrastructure, licensing, and maintenance costs into a single comprehensive CostEstimate object.\n"
        "Ensure the final total_estimated_cost perfectly matches the sum of all components."
    )
    
    # We pass the message history so the LLM can see what the tools returned
    messages = [{"role": "system", "content": sys_prompt}]
    
    if state.get("messages"):
        messages.extend(state["messages"])
        
    estimate = await llm.ainvoke(messages)
    
    return {"cost_estimate": estimate}
