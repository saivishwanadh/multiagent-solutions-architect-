from src.schemas.state import SupervisorState
from src.config.settings import get_llm
from langchain_core.prompts import ChatPromptTemplate

async def node_direct_qa(state: SupervisorState) -> dict:
    """Answers follow-up questions about the proposal directly."""
    
    prev = state.get("working_outputs", {}).get("previous_final_output")
    if not prev:
        return {"runtime_state": {"qa_response": "I don't have a previous proposal to answer questions about. Please state your project request."}}
        
    from langchain_core.tools import tool
    from src.tools.file_tools import save_document
    
    @tool
    def generate_markdown_document() -> str:
        """Use this tool when the user asks to save, download, generate, or create a document/file for the project proposal."""
        md_content = state.get("working_outputs", {}).get("markdown_report")
        if md_content:
            return save_document(md_content)
        return "Error: No markdown report available in memory."
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an Enterprise Solutions Architect answering a follow-up question about the project proposal you just created.\n\nProposal Context:\n{context}"),
        ("user", "{question}")
    ])
    
    llm = get_llm(temperature=0.3).bind_tools([generate_markdown_document])
    chain = prompt | llm
    
    context = (
        f"Project: {prev.project_name}\n"
        f"Summary: {prev.executive_summary.objective}\n"
        f"Cost: ${prev.total_cost:,.0f} (Budget: {prev.budget_status})\n"
        f"Risks: {[r.description for r in prev.top_risks]}\n"
        f"Tech Stack: {prev.tech_stack.backend.name if prev.tech_stack.backend else 'Unknown'}\n"
    )
    
    question = state.get("persistent_context", {}).get("latest_user_prompt", "")
    result = await chain.ainvoke({"context": context, "question": question})
    
    # Check if the LLM decided to call the tool
    if result.tool_calls:
        for tc in result.tool_calls:
            if tc["name"] == "generate_markdown_document":
                # Execute the tool manually
                filepath = generate_markdown_document.invoke({})
                if "Error" in filepath:
                    return {"runtime_state": {"qa_response": "I couldn't find a generated markdown report in memory to save. Please run a new project request."}}
                return {"runtime_state": {"qa_response": f"I have successfully generated and saved your project proposal to: **{filepath}**"}}
                
    content = result.content
    if isinstance(content, list):
        text_parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
        content = "".join(text_parts) if text_parts else str(content)
        
    return {"runtime_state": {"qa_response": content}}
