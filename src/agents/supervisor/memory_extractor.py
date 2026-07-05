from pydantic import BaseModel, Field
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from src.config.settings import get_llm
from src.memory.vector_store import OrgLessonsMemory
from src.schemas.final_blueprint import FinalBlueprint

class MemoryLesson(BaseModel):
    category: str = Field(description="Broad category e.g., 'Architecture', 'Finance', 'Security'")
    context: str = Field(description="The specific context or mistake that happened in this project.")
    lesson: str = Field(description="The core lesson learned (e.g. 'Local on-premise deployments increase timeline').")
    directive: str = Field(description="The strict rule to apply to future projects (e.g. 'Always add a baseline of 4 weeks').")

class ExtractedLessons(BaseModel):
    lessons: List[MemoryLesson] = Field(description="List of 1 to 3 critical lessons learned from this project execution.")

def get_memory_extractor_agent():
    system_prompt = (
        "You are the Organizational Memory Extractor.\n"
        "Your job is to analyze the final project proposal (especially any budget overruns, severe risks, or rejected feasibilities) "
        "and extract 1 to 3 HARD organizational lessons learned.\n"
        "These lessons will be saved into a vector database to protect future AI agents from making the same mistakes.\n"
        "If the project went perfectly, extract a positive best-practice rule.\n"
        "Keep the lessons strict, specific, and actionable."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Extract memory from this final project proposal:\n\n{final_proposal_json}")
    ])
    
    llm = get_llm(temperature=0.2).with_structured_output(ExtractedLessons)
    return prompt | llm

async def node_extract_lessons(state: dict) -> dict:
    """Extracts lessons from the FinalBlueprint and saves them to ChromaDB."""
    final = state.get("working_outputs", {}).get("final_output")
    if not final or not isinstance(final, FinalBlueprint):
        return {}
        
    try:
        agent = get_memory_extractor_agent()
        result = await agent.ainvoke({"final_proposal_json": final.model_dump_json()})
        
        memory_store = OrgLessonsMemory.get_instance()
        
        print(f"\n[Memory Extractor] Extracted {len(result.lessons)} organizational lessons.")
        for lesson in result.lessons:
            memory_store.add_lesson(
                category=lesson.category,
                context=lesson.context,
                lesson=lesson.lesson,
                directive=lesson.directive
            )
            
    except Exception as e:
        print(f"\n[Memory Extractor] Failed to extract or save memory: {e}")
        
    # We do not modify the state, we just perform a side effect.
    return {}
