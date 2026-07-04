import os
import json
import asyncio
from typing import Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.runnables import RunnableConfig

from src.schemas.state import SupervisorState
from src.routing.category_router import route_by_category

# Sub-graphs and Agents
from src.graphs.scope_subgraph import build_scope_subgraph
from src.graphs.finance_subgraph import build_finance_subgraph
from src.graphs.risk_subgraph import build_risk_subgraph
from src.agents.supervisor import (
    process_input,
    node_intake_analyzer,
    process_synthesis,
    node_proposal_generator,
    node_scenario_splitter,
    node_scenario_comparator,
    node_direct_qa,
    node_clarification,
    node_optimization_router,
    node_invoke_hitl
)
from src.agents.supervisor.memory_extractor import node_extract_lessons

# Pre-compile sub-graphs once at module load (avoids re-compiling on every call)
_scope_graph = build_scope_subgraph()
_finance_graph = build_finance_subgraph()
_risk_graph = build_risk_subgraph()

async def node_init_state(state: SupervisorState) -> SupervisorState:
    """Initializes default state values."""
    
    # Initialize defaults if not present
    if "conflict_loop_count" not in state: state["conflict_loop_count"] = 0
    if "total_hitl_count" not in state: state["total_hitl_count"] = 0
    if "negotiation_history" not in state: state["negotiation_history"] = []
    if "messages" not in state: state["messages"] = []
    return state

async def node_smart_reset(state: SupervisorState) -> SupervisorState:
    """Intelligently resets execution state based on execution_intent."""
    if state.get("final_output"):
        state["previous_final_output"] = state["final_output"]
        
    vi = state.get("validated_input")
    intent = vi.execution_intent if vi and hasattr(vi, "execution_intent") else "new_project"
    
    if intent == "follow_up":
        # Do not reset anything, just preserve the state for Q&A
        pass
    else:
        keys_to_clear = [
            "cost_estimate", "risk_assessment",
            "conflict_feedback", "deadlock_options", "user_choice", "final_output",
            "scenario_a_result", "scenario_b_result", "scenario_comparison", "refinement_target",
            "delta_summary", "qa_response"
        ]
        
        if intent == "new_project":
            keys_to_clear.append("project_blueprint")
            
        for k in keys_to_clear:
            state[k] = None
            
        state["conflict_loop_count"] = 0

    return state



async def node_result_aggregator(state: SupervisorState) -> SupervisorState:
    """Merges all sub-graph outputs. (Pass-through for now since state handles it)."""
    return state

async def node_constraint_validator(state: SupervisorState) -> SupervisorState:
    """Checks budget and feasibility. Placeholder for Phase 11."""
    return state

def check_conflicts(state: SupervisorState) -> str:
    from src.routing.conflict_loop import check_conflicts as _check_conflicts
    return _check_conflicts(state)

async def node_generate_feedback(state: SupervisorState) -> SupervisorState:
    from src.routing.conflict_loop import generate_conflict_feedback
    return generate_conflict_feedback(state)

def route_refinement(state: SupervisorState) -> str:
    target = state.get("refinement_target", "scope")
    if target == "architecture":
        return "invoke_architecture"
    elif target == "both":
        return "invoke_scope" # runs scope then arch
    return "invoke_scope"

def route_after_hitl(state: SupervisorState) -> str:
    return "invoke_scope"





async def node_compute_delta(state: SupervisorState) -> SupervisorState:
    old = state.get("previous_final_output")
    new_cost = state.get("cost_estimate")
    if old and new_cost:
        old_cost = old.total_cost
        delta_cost = new_cost.total_estimated_cost - old_cost
        state["delta_summary"] = f"Cost changed by ${delta_cost:,.2f}"
    return state



def should_clarify(state: SupervisorState) -> str:
    vi = state.get("validated_input")
    if vi and vi.missing_info:
        critical_missing = [m for m in vi.missing_info if "budget" in m.lower() or "timeline" in m.lower()]
        if critical_missing and vi.query_category in (1, 3):
            return "clarify"
    return route_by_category(state)




async def node_invoke_scope(state: SupervisorState, config: RunnableConfig) -> dict:
    res = await _scope_graph.ainvoke(state, config)
    return {"scope_output": res.get("project_blueprint")}

async def node_invoke_finance(state: SupervisorState, config: RunnableConfig) -> dict:
    s = dict(state)
    s["messages"] = [] # Reset messages for tool node loop
    s["project_blueprint"] = state.get("scope_output")
    res = await _finance_graph.ainvoke(s, config)
    return {"cost_estimate": res.get("cost_estimate")}

async def node_invoke_risk(state: SupervisorState, config: RunnableConfig) -> dict:
    s = dict(state)
    s["project_blueprint"] = state.get("scope_output")
    res = await _risk_graph.ainvoke(s, config)
    return {"risk_assessment": res.get("risk_assessment")}

def build_supervisor_graph():
    """Builds the supervisor graph structure (without checkpointer)."""
    graph = StateGraph(SupervisorState)
    
    graph.add_node("init_state", node_init_state)
    graph.add_node("intake_analyzer", node_intake_analyzer)
    graph.add_node("smart_reset", node_smart_reset)
    
    # Add wrapped subgraphs
    graph.add_node("invoke_scope", node_invoke_scope)
    graph.add_node("invoke_finance", node_invoke_finance)
    graph.add_node("invoke_risk", node_invoke_risk)

    graph.add_node("result_aggregator", node_result_aggregator)
    graph.add_node("constraint_validator", node_constraint_validator)
    graph.add_node("proposal_generator", node_proposal_generator)
    graph.add_node("direct_qa", node_direct_qa)
    
    graph.add_node("optimization_router", node_optimization_router)
    graph.add_node("generate_feedback", node_generate_feedback)
    graph.add_node("hitl_handler", node_invoke_hitl)
    graph.add_node("memory_extractor", node_extract_lessons)
    
    graph.add_node("clarification", node_clarification)
    graph.add_node("scenario_splitter", node_scenario_splitter)
    graph.add_node("scenario_comparator", node_scenario_comparator)
    graph.add_node("compute_delta", node_compute_delta)
    
    graph.add_edge(START, "init_state")
    graph.add_edge("init_state", "intake_analyzer")
    graph.add_edge("intake_analyzer", "smart_reset")
    
    route_mapping = {
        "clarify": "clarification",
        "reject": END,
        "full_pipeline": "invoke_scope",
        "architecture_first": "invoke_scope",
        "tradeoff": "scenario_splitter",
        "pivot": "invoke_scope",
        "direct_qa": "direct_qa"
    }
    
    graph.add_conditional_edges("smart_reset", should_clarify, route_mapping)
    graph.add_conditional_edges("clarification", route_by_category, route_mapping)
    
    # Tradeoff path
    graph.add_edge("scenario_splitter", "scenario_comparator")
    graph.add_edge("scenario_comparator", END)
    
    # Main pipeline: Scope -> [Finance, Risk] -> Aggregator
    graph.add_edge("invoke_scope", "invoke_finance")
    graph.add_edge("invoke_scope", "invoke_risk")
    
    graph.add_edge("invoke_finance", "result_aggregator")
    graph.add_edge("invoke_risk", "result_aggregator")
    
    graph.add_edge("result_aggregator", "constraint_validator")
    
    graph.add_conditional_edges("constraint_validator", check_conflicts, {
        "pass": "compute_delta",
        "conflict": "optimization_router",
        "deadlock": "hitl_handler"
    })
    
    graph.add_edge("compute_delta", "proposal_generator")
    graph.add_edge("proposal_generator", END)
    graph.add_edge("direct_qa", END)
    
    graph.add_edge("hitl_handler", "invoke_scope")
    
    graph.add_edge("optimization_router", "generate_feedback")
    
    graph.add_edge("generate_feedback", "invoke_scope")
    
    graph.add_edge("proposal_generator", "memory_extractor")
    graph.add_edge("memory_extractor", END)
    return graph


# Database path for persistent state (handled by callers)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "memory.db")


