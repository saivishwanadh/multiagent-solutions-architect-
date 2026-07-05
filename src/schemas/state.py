"""
Global Supervisor State schema.

This is the main state object that flows through the LangGraph
Parent Supervisor Graph. It holds the outputs of all agents,
conflict loop tracking, and human-in-the-loop (HITL) state.
"""

from typing import Annotated, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage

from src.schemas.validated_input import ValidatedInput
from src.schemas.blueprint import ProjectBlueprint
from src.schemas.cost_estimate import CostEstimate
from src.schemas.risk_assessment import RiskAssessment
from src.schemas.final_blueprint import FinalBlueprint
from src.schemas.conflict_feedback import ConflictFeedback
from src.schemas.scenario_comparison import ScenarioComparison


class PersistentContext(TypedDict, total=False):
    initial_user_prompt: str | None
    latest_user_prompt: str | None
    parsed_requirements: str | None
    business_constraints: ValidatedInput | None
    negotiation_history: list[dict[str, Any]]
    total_hitl_count: int

class WorkingOutputs(TypedDict, total=False):
    scope_output: ProjectBlueprint | None
    cost_estimate: CostEstimate | None
    risk_assessment: RiskAssessment | None
    final_output: FinalBlueprint | None
    previous_final_output: FinalBlueprint | None
    markdown_report: str | None

class RuntimeState(TypedDict, total=False):
    conflict_loop_count: int
    conflict_feedback: ConflictFeedback | None
    refinement_target: str | None
    deadlock_options: list[dict[str, Any]] | None
    user_choice: str | None
    scenario_comparison: ScenarioComparison | None
    scenario_a_result: dict | None
    scenario_b_result: dict | None
    delta_summary: str | None
    qa_response: str | None

def merge_dict(old: dict | None, new: dict | None) -> dict:
    if not old:
        return new or {}
    if not new:
        return old
    merged = old.copy()
    merged.update(new)
    return merged

class SupervisorState(TypedDict):
    """
    The main state schema for the Multi-Agent Orchestration graph.
    Uses strict layers to prevent context pruning and state bloat.
    """
    user_prompt: str | None
    messages: Annotated[list[BaseMessage], lambda old, new: old + new]
    
    # Nested State Layers
    persistent_context: Annotated[PersistentContext, merge_dict]
    working_outputs: Annotated[WorkingOutputs, merge_dict]
    runtime_state: Annotated[RuntimeState, merge_dict]
