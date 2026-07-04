from src.schemas.state import SupervisorState
from src.config.settings import get_llm
from langchain_core.prompts import ChatPromptTemplate

async def node_direct_qa(state: SupervisorState) -> dict:
    """Answers follow-up questions about the proposal directly."""
    
    prev = state.get("previous_final_output")
    if not prev:
        return {"qa_response": "I don't have a previous proposal to answer questions about. Please state your project request."}
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an Enterprise Solutions Architect answering a follow-up question about the project proposal you just created.\n\nProposal Context:\n{context}"),
        ("user", "{question}")
    ])
    
    llm = get_llm(temperature=0.3)
    chain = prompt | llm
    
    context = (
        f"Project: {prev.project_name}\n"
        f"Summary: {prev.executive_summary}\n"
        f"Cost: ${prev.total_cost:,.0f} (Budget: {prev.budget_status})\n"
        f"Risks: {[r.description for r in prev.top_risks]}\n"
        f"Tech Stack: {prev.tech_stack}\n"
    )
    
    result = await chain.ainvoke({"context": context, "question": state["user_prompt"]})
    return {"qa_response": result.content}
