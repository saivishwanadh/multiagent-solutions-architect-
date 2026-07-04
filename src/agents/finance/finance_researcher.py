from src.config.settings import get_llm
from src.agents.finance.state import FinanceState
from src.tools.financial_tools import finance_tools
from src.agents.finance.utils import read_finance_prompt

async def node_finance_researcher(state: FinanceState) -> dict:
    """Uses parallel tool calling to gather cost metrics instantly."""
    llm = get_llm(temperature=0.0).bind_tools(finance_tools)
    
    msgs = state.get("messages") or []
    new_msgs = []
    
    if not msgs:
        sys_prompt = (
            "You are the Finance Researcher. Your job is to gather raw cost data for the upcoming project.\n"
            "CRITICAL: You MUST use your provided tools to fetch cloud pricing, developer cost, and licensing.\n"
            "If the exact cloud pricing is unknown, use the `search_live_pricing` tool to search the live internet for current market rates.\n"
            "CRITICAL: Call ALL the tools you need IN PARALLEL at the exact same time. Do not call one, wait, and call another.\n"
            "Once you have called the tools and received the data, simply say 'RESEARCH COMPLETE'."
        )
        
        content = f"Tech Stack:\n{state['project_blueprint'].tech_stack.model_dump_json()}\n"
        if state["project_blueprint"].infrastructure_plan:
            content += f"Infrastructure Plan:\n{state['project_blueprint'].infrastructure_plan.model_dump_json()}\n"
            
        # Optional: Add features if they need to know team size or timeline
        
        new_msgs = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": content}
        ]
        msgs = new_msgs
        
    res = await llm.ainvoke(msgs)
    new_msgs.append(res)
    return {"messages": new_msgs}
