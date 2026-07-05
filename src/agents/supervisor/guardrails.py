"""
Agent 0 (Input Guardrails).

Validates the user prompt, classifies it into one of 5 categories,
and extracts explicit constraints.
"""

import os
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from src.config.settings import get_llm
from src.schemas.validated_input import ValidatedInput

# Determine the path to the prompt file
PROMPT_PATH = Path(__file__).parent.parent.parent / "config" / "prompts" / "guardrails.txt"

def load_system_prompt() -> str:
    """Loads the system prompt from the configuration file."""
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()

def get_guardrails_agent():
    """
    Constructs the guardrails agent pipeline.
    Uses LCEL (LangChain Expression Language) to chain the prompt, LLM,
    and structured output parser.
    """
    system_prompt = load_system_prompt()
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Context: {context}\n\nUser Input: {user_input}")
    ])
    
    # Initialize the LLM
    llm = get_llm(temperature=0.0) # We want consistent classification
    
    # Bind the Pydantic schema to the LLM to guarantee structured output
    structured_llm = llm.with_structured_output(ValidatedInput)
    
    # Create the runnable chain
    chain = prompt_template | structured_llm
    
    return chain

async def process_input(user_input: str, context: str = "") -> ValidatedInput:
    """
    Runs the user input through the guardrails agent.
    """
    agent = get_guardrails_agent()
    result = await agent.ainvoke({"user_input": user_input, "context": context})
    return result

async def node_intake_analyzer(state: dict) -> dict:
    """Validates, classifies, and extracts constraints from the user prompt."""
    context = ""
    prev = state.get("working_outputs", {}).get("previous_final_output")
    if prev:
        context = f"Previous Project Context: {prev.project_name} - {prev.executive_summary}"
        
    user_input = state.get("user_prompt") or state.get("persistent_context", {}).get("latest_user_prompt", "")
    vi = await process_input(user_input, context)
    
    return {"persistent_context": {"business_constraints": vi}}

if __name__ == "__main__":
    # Standalone testing of Agent 0
    import json
    
    print("=== Agent 0 (Input Guardrails) Standalone Test ===")
    
    test_prompts = [
        "Can we build a medical parser for $12k in 4 weeks?",
        "Which vector DB should we use for 50M embeddings?",
        "How many engineers for an invoice pipeline?",
        "What if we switch from AWS to local on-premise servers?",
        "Add voice-to-text to the previous RAG project",
        "We need to implement SAP S/4HANA for our manufacturing plant. Budget is 2 million, timeline is 8 months.",
        "What's the weather today?",
        "asdfghjkl"
    ]
    
    for idx, prompt in enumerate(test_prompts, 1):
        print(f"\n--- Test {idx} ---")
        print(f"Input: \"{prompt}\"")
        try:
            output = process_input(prompt)
            print(f"Valid: {output.is_valid}")
            if output.is_valid:
                print(f"Category: {output.query_category}")
                print(f"Type: {output.project_type}")
                print(f"Summary: {output.project_summary}")
                print(f"Constraints: {output.constraints.model_dump_json(exclude_none=True)}")
            else:
                print(f"Rejection Reason: {output.rejection_reason}")
        except Exception as e:
            print(f"Error: {e}")
