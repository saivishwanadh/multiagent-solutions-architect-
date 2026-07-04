from src.config.settings import get_llm
from src.agents.scope.state import ScopeState, ArchitectureDesign
from src.agents.scope.utils import read_scope_prompt
from src.agents.scope.utils import read_scope_prompt
from src.memory.vector_store import get_lessons
from src.utils.formatters import format_features

async def node_architecture_designer(state: ScopeState) -> dict:
    """
    Combined node that handles tech stack, architecture pattern, and infrastructure.
    """
    llm = get_llm(temperature=0.0).with_structured_output(ArchitectureDesign)
    
    sys_prompt = read_scope_prompt("architecture_designer.txt")
    
    features_text = format_features(state.get("features") or [])
    content = f"Project Type: {state['validated_input'].project_type}\n"
    content += f"Tech Preferences: {state['validated_input'].constraints.tech_preferences}\n"
    content += f"Features:\n{features_text}\n"
    
    # Query ChromaDB for Long-Term Cross-Thread Memory
    search_query = f"Architecture for {state['validated_input'].project_type} using {state['validated_input'].constraints.tech_preferences}"
    past_lessons = get_lessons(search_query, k=2)
    if past_lessons:
        content += "\n\nCRITICAL ORGANIZATIONAL MEMORY (Apply these rules from past projects):\n"
        for i, lesson in enumerate(past_lessons):
            content += f"{i+1}. {lesson}\n"

    
    if state.get("conflict_feedback"):
        cf = state["conflict_feedback"]
        content += f"\n\nCRITICAL OPTIMIZATION NEEDED (Iteration {cf.iteration_number}):\n"
        content += f"Guidance: {cf.guidance}\n"
        content += "You MUST pick cheaper, lighter-weight technologies and scaling strategies to reduce costs.\n"
        
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": content}
    ]
    
    arch_data = await llm.ainvoke(messages)
    
    return {
        "architecture_design": arch_data
    }
