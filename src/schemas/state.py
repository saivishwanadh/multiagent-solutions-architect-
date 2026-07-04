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


class SupervisorState(TypedDict):
    """
    The state schema for the Multi-Agent Orchestration graph.
    All keys can be optional or None before the respective agent runs.
    """

    # === PERSISTENT STATE (Retained across turns) ===
    user_prompt: str
    messages: Annotated[list[BaseMessage], lambda old, new: old + new]
    previous_final_output: FinalBlueprint | None
    validated_input: ValidatedInput | None
    total_hitl_count: int
    negotiation_history: list[dict[str, Any]]

    # === TEMPORARY EXECUTION STATE (Reset based on Execution Intent) ===
    scope_output: ProjectBlueprint | None            # Sub-graph A (Scope)
    cost_estimate: CostEstimate | None               # Sub-graph C
    risk_assessment: RiskAssessment | None           # Sub-graph D
    final_output: FinalBlueprint | None              # Proposal Generator (Agent S)
    
    conflict_loop_count: int
    conflict_feedback: ConflictFeedback | None
    refinement_target: str | None   # "scope" | "architecture" | "both"
    
    deadlock_options: list[dict[str, Any]] | None
    user_choice: str | None

    scenario_comparison: ScenarioComparison | None
    scenario_a_result: dict | None
    scenario_b_result: dict | None

    delta_summary: str | None
    qa_response: str | None
