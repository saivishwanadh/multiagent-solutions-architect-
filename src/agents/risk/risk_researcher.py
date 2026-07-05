from src.config.settings import get_llm
from src.agents.risk.state import RiskState
from src.tools.risk_tools import risk_tools

async def node_risk_researcher(state: dict) -> dict:
    """Uses parallel tool calling to search the live web for vulnerabilities."""
    llm = get_llm(temperature=0.0).bind_tools(risk_tools)
    
    msgs = state.get("messages") or []
    new_msgs = []
    
    if not msgs:
        sys_prompt = (
            "You are the Risk Researcher. Your job is to search the live web for recent security vulnerabilities.\n"
            "CRITICAL: You MUST use the `search_recent_vulnerabilities` tool to check the project's tech stack.\n"
            "Once you have called the tools and received the data, simply say 'RESEARCH COMPLETE'."
        )
        
        bp = state.get("project_blueprint")
        if bp and bp.tech_stack:
            tech_list = []
            if bp.tech_stack.frontend: tech_list.append(bp.tech_stack.frontend.name)
            if bp.tech_stack.backend: tech_list.append(bp.tech_stack.backend.name)
            if bp.tech_stack.database: tech_list.append(bp.tech_stack.database.name)
            if bp.tech_stack.infrastructure: tech_list.append(bp.tech_stack.infrastructure.name)
            
            for t in bp.tech_stack.enterprise_platforms: tech_list.append(t.name)
            for t in bp.tech_stack.integrations: tech_list.append(t.name)
            
            content = f"Tech Stack:\n{', '.join(tech_list)}"
        else:
            content = "Tech Stack: Unknown"
            
        new_msgs = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": content}
        ]
        msgs = new_msgs
        
    res = await llm.ainvoke(msgs)
    new_msgs.append(res)
    return {"messages": new_msgs}
