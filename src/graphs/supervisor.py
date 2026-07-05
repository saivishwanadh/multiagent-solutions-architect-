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

async def node_init_state(state: SupervisorState) -> dict:
    """Initializes default state values."""
    pc_updates = {}
    rs_updates = {}
    
    if "conflict_loop_count" not in state.get("runtime_state", {}): 
        rs_updates["conflict_loop_count"] = 0
    if "total_hitl_count" not in state.get("persistent_context", {}): 
        pc_updates["total_hitl_count"] = 0
    if "negotiation_history" not in state.get("persistent_context", {}): 
        pc_updates["negotiation_history"] = []
    
    # Capture initial prompt
    if state.get("user_prompt"):
        if not state.get("persistent_context", {}).get("initial_user_prompt"):
            pc_updates["initial_user_prompt"] = state["user_prompt"]
        pc_updates["latest_user_prompt"] = state["user_prompt"]
        
    return {"persistent_context": pc_updates, "runtime_state": rs_updates}

async def node_smart_reset(state: SupervisorState) -> dict:
    """Intelligently resets execution state based on execution_intent."""
    wo_updates = {}
    rs_updates = {}
    
    if state.get("working_outputs", {}).get("final_output"):
        wo_updates["previous_final_output"] = state.get("working_outputs", {})["final_output"]
        
    vi = state.get("persistent_context", {}).get("business_constraints")
    intent = vi.execution_intent if vi and hasattr(vi, "execution_intent") else "new_project"
    
    if intent == "follow_up":
        # Do not reset anything, just preserve the state for Q&A
        pass
    else:
        keys_to_clear_wo = ["cost_estimate", "risk_assessment", "final_output"]
        keys_to_clear_rs = [
            "conflict_feedback", "deadlock_options", "user_choice", 
            "scenario_a_result", "scenario_b_result", "scenario_comparison", 
            "refinement_target", "delta_summary", "qa_response"
        ]
        
        if intent == "new_project":
            keys_to_clear_wo.append("scope_output")
            
        for k in keys_to_clear_wo:
            wo_updates[k] = None
        for k in keys_to_clear_rs:
            rs_updates[k] = None
            
        rs_updates["conflict_loop_count"] = 0

    return {"working_outputs": wo_updates, "runtime_state": rs_updates}



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
    target = state.get("runtime_state", {}).get("refinement_target") or "scope"
    if target == "architecture":
        return "invoke_architecture"
    elif target == "both":
        return "invoke_scope" # runs scope then arch
    return "invoke_scope"

def route_after_hitl(state: SupervisorState) -> str:
    return "invoke_scope"





async def node_compute_delta(state: SupervisorState) -> SupervisorState:
    old = state.get("working_outputs", {}).get("previous_final_output")
    new_cost = state.get("working_outputs", {}).get("cost_estimate")
    if old and new_cost:
        old_cost = old.total_cost
        delta_cost = new_cost.total_estimated_cost - old_cost
        return {"runtime_state": {"delta_summary": f"Cost changed by ${delta_cost:,.2f}"}}
    return {}



def should_clarify(state: SupervisorState) -> str:
    vi = state.get("persistent_context", {}).get("business_constraints")
    
    if vi:
        missing_info = getattr(vi, "missing_info", vi.get("missing_info", []) if isinstance(vi, dict) else [])
        query_category = getattr(vi, "query_category", vi.get("query_category", 1) if isinstance(vi, dict) else 1)
        
        if missing_info:
            critical_missing = [m for m in missing_info if "budget" in m.lower() or "timeline" in m.lower()]
            if critical_missing and query_category in (1, 3):
                return "clarify"
                
    return route_by_category(state)




async def node_invoke_scope(state: SupervisorState, config: RunnableConfig) -> dict:
    # Explicit context projection for Scope
    s = {
        "messages": [],
        "validated_input": state.get("persistent_context", {}).get("business_constraints"),
        "initial_user_prompt": state.get("persistent_context", {}).get("initial_user_prompt"),
        "latest_user_prompt": state.get("persistent_context", {}).get("latest_user_prompt"),
        "negotiation_history": state.get("persistent_context", {}).get("negotiation_history", []),
        "previous_final_output": state.get("working_outputs", {}).get("previous_final_output"),
        "conflict_feedback": state.get("runtime_state", {}).get("conflict_feedback")
    }
    res = await _scope_graph.ainvoke(s, config)
    
    pc = {}
    if res.get("parsed_requirements"):
        pc["parsed_requirements"] = res["parsed_requirements"]
        
    return {
        "persistent_context": pc, 
        "working_outputs": {"scope_output": res.get("project_blueprint")}
    }

async def node_invoke_finance(state: SupervisorState, config: RunnableConfig) -> dict:
    # Explicit context projection for Finance
    s = {
        "messages": [],
        "project_blueprint": state.get("working_outputs", {}).get("scope_output"),
        "parsed_requirements": state.get("persistent_context", {}).get("parsed_requirements"),
        "validated_input": state.get("persistent_context", {}).get("business_constraints")
    }
    res = await _finance_graph.ainvoke(s, config)
    
    return {"working_outputs": {"cost_estimate": res.get("cost_estimate")}}

async def node_invoke_risk(state: SupervisorState, config: RunnableConfig) -> dict:
    # Explicit context projection for Risk
    s = {
        "messages": [],
        "project_blueprint": state.get("working_outputs", {}).get("scope_output"),
        "parsed_requirements": state.get("persistent_context", {}).get("parsed_requirements"),
        "validated_input": state.get("persistent_context", {}).get("business_constraints")
    }
    res = await _risk_graph.ainvoke(s, config)
    
    return {"working_outputs": {"risk_assessment": res.get("risk_assessment")}}

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


