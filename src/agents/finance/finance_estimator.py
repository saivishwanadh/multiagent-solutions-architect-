from src.config.settings import get_llm
from src.schemas.cost_estimate import CostEstimate
from src.agents.finance.state import FinanceState

async def node_finance_estimator(state: FinanceState) -> dict:
    """Generates the final CostEstimate using data gathered by the researcher."""
    llm = get_llm(temperature=0.0).with_structured_output(CostEstimate)
    
    sys_prompt = (
        "You are the Finance Estimator. Review the tool outputs from the Finance Researcher.\n"
        "Compile all development, infrastructure, licensing, and maintenance costs into a single comprehensive CostEstimate object.\n"
        "Ensure the final total_estimated_cost perfectly matches the sum of all components.\n\n"
        "CRITICAL ENTERPRISE ESTIMATION RULES:\n"
        "1. SCALE REALISTICALLY: For massive projects (e.g., millions of IoT events, global deployments), infrastructure costs should be in the tens/hundreds of thousands of dollars per month, not a few hundred. Do NOT underestimate cloud costs.\n"
        "2. TEAM SIZING: An enterprise project requires a full team. Populate the `team_composition` array with realistic roles (e.g., Solution Architect, Backend Engineer, QA Engineer, DevOps, IoT Engineer, etc.). Total headcounts for global projects should be 12-25+ people. Set a realistic `monthly_rate` for each.\n"
        "3. TIMELINE PRESERVATION: NEVER arbitrarily compress the user's requested timeline to save money. If the context implies or asks for 12 months (48 weeks), you MUST estimate for 48 weeks.\n"
        "4. BASIS OF ESTIMATE: You must justify your numbers. Provide 3-5 statements in `basis_of_estimate` explaining HOW you got your numbers (e.g., 'Estimated 3 ML Engineers for 6 months at $15k/mo', 'AWS IoT Core pricing modeled for 1M events/sec').\n\n"
        f"--- FULL BUSINESS CONTEXT (PARSED REQUIREMENTS) ---\n"
        f"{state.get('parsed_requirements', 'No parsed requirements available.')}\n"
        f"----------------------------------------------------\n"
    )
    
    # We pass the message history so the LLM can see what the tools returned
    messages = [{"role": "system", "content": sys_prompt}]
    
    if state.get("messages"):
        messages.extend(state["messages"])
        
    estimate = await llm.ainvoke(messages)
    
    return {"cost_estimate": estimate}
