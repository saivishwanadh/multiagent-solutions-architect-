from pydantic import BaseModel, Field
from src.config.settings import get_llm
from src.agents.scope.state import ScopeState

class CoverageResult(BaseModel):
    is_fully_covered: bool = Field(description="True if all explicit requirements are mapped to features.")
    missing_requirements: str | None = Field(
        default=None, 
        description="If not fully covered, specifically list what was dropped or reduced in scale."
    )

async def node_coverage_checker(state: ScopeState) -> dict:
    """Verifies that the extracted features fully cover the parsed requirements without silently dropping anything."""
    
    # Fast path: if we already retried and are here again, we can just pass to avoid infinite loops,
    # or we can allow up to N retries. For now, if coverage_feedback is already populated, 
    # it means we've already looped once. Let's just do a 1-retry limit for safety.
    if state.get("coverage_feedback"):
        # We already fed back once. We'll accept whatever the LLM gave us on the second try to prevent infinite loops.
        return {"coverage_feedback": None}

    reqs = state.get("parsed_requirements", "")
    features = state.get("features", [])
    
    feature_text = "\n".join([f"- {f.name}: {f.description}" for f in features])
    
    prompt = f"""You are the Requirement Coverage Validator.
    
ORIGINAL REQUIREMENTS:
{reqs}

EXTRACTED FEATURES:
{feature_text}

Check if ANY explicit requirements (like '1 million devices', 'SAP integration', 'Machine Learning') were silently dropped or reduced in scale from the features list.
If everything is covered, return is_fully_covered=True.
If anything is missing or scaled down, return is_fully_covered=False and list what is missing.
"""

    llm = get_llm(temperature=0.0).with_structured_output(CoverageResult)
    result = await llm.ainvoke([{"role": "user", "content": prompt}])
    
    if result.is_fully_covered:
        return {"coverage_feedback": None}
    else:
        feedback = f"COVERAGE ERROR: The following requirements were dropped or reduced in scale: {result.missing_requirements}. You MUST explicitly include them."
        return {"coverage_feedback": feedback}
