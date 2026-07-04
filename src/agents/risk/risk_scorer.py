from src.config.settings import get_llm
from src.schemas.risk_assessment import RiskAssessment
from src.agents.risk.utils import read_risk_prompt
from src.memory.vector_store import get_lessons
from src.utils.formatters import format_risks

async def node_risk_summary(state: dict) -> dict:
    llm = get_llm(temperature=0.0).with_structured_output(RiskAssessment)
    sys_prompt = read_risk_prompt("risk_scorer.txt")
    
    all_risks = (state.get("timeline_risks") or []) + (state.get("technical_risks") or []) + (state.get("security_risks") or [])
    risks_text = format_risks(all_risks)
    content = f"Identified Risks:\n{risks_text}\n"
    
    # Query ChromaDB for Long-Term Cross-Thread Memory to flag historical risks
    bp = state.get("project_blueprint")
    if bp:
        search_query = f"Risk timeline overruns feasibility for {bp.project_type}"
        past_lessons = get_lessons(search_query, k=2)
        if past_lessons:
            content += "\n\nCRITICAL HISTORICAL RISKS (You must flag these if applicable to this project):\n"
            for i, lesson in enumerate(past_lessons):
                content += f"{i+1}. {lesson}\n"

    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": content}
    ]
    
    # Inject Live Web Search results if available
    if state.get("messages"):
        messages.extend(state["messages"])
        
    assessment = await llm.ainvoke(messages)
    
    # Backfill if LLM didn't copy risks properly
    if not assessment.risks:
        assessment.risks = all_risks
        
    return {"risk_assessment": assessment}
