from typing import TypedDict, Any
from langgraph.graph import StateGraph, START, END

from src.schemas.validated_input import ValidatedInput
from src.schemas.conflict_feedback import ConflictFeedback
from src.schemas.blueprint import ProjectBlueprint, Feature, Milestone
from src.agents.scope import (
    ScopeState,
    node_requirement_parser, 
    node_feature_extractor, 
    node_architecture_designer,
    node_milestone_planner,
    ArchitectureDesign
)

async def node_scope_summary(state: ScopeState) -> dict:
    """Assembles the final ProjectBlueprint from the preceding nodes."""
    arch = state.get("architecture_design")
    
    bp = ProjectBlueprint(
        project_name=f"{state['validated_input'].project_type.replace('_', ' ').title()} Project",
        project_type=state["validated_input"].project_type,
        features=state.get("features", []),
        tech_stack=arch.tech_stack if arch else None,
        architecture_pattern=arch.architecture_pattern if arch else None,
        infrastructure_plan=arch.infrastructure_plan if arch else None,
        alternatives_considered=arch.alternatives_considered if arch else [],
        milestones=state.get("milestones", []),
        confidence_score=85
    )
    return {"project_blueprint": bp}

def build_scope_subgraph():
    graph = StateGraph(ScopeState)
    
    graph.add_node("requirement_parser", node_requirement_parser)
    graph.add_node("feature_extractor", node_feature_extractor)
    graph.add_node("architecture_designer", node_architecture_designer)
    graph.add_node("milestone_planner", node_milestone_planner)
    graph.add_node("scope_summary", node_scope_summary)
    
    graph.add_edge(START, "requirement_parser")
    graph.add_edge("requirement_parser", "feature_extractor")
    graph.add_edge("feature_extractor", "architecture_designer")
    graph.add_edge("architecture_designer", "milestone_planner")
    graph.add_edge("milestone_planner", "scope_summary")
    graph.add_edge("scope_summary", END)
    
    return graph.compile()
