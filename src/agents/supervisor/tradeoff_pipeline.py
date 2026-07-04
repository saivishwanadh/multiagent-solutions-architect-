async def run_pipeline_for_scenario(prompt: str, lessons: list[dict] = None) -> dict:
    """Helper to run the sub-graphs sequentially for a specific scenario prompt."""
    from src.agents.supervisor.guardrails import process_input
    from src.graphs.scope_subgraph import build_scope_subgraph
    from src.graphs.finance_subgraph import build_finance_subgraph
    from src.graphs.risk_subgraph import build_risk_subgraph
    
    vi = await process_input(prompt)
    
    # 1. Scope
    scope_graph = build_scope_subgraph()
    scope_result = await scope_graph.ainvoke({
        "validated_input": vi,
        "conflict_feedback": None,
        "negotiation_history": [],
        "parsed_requirements": None,
        "features": None,
        "milestones": None,
        "project_blueprint": None,
        "previous_final_output": None
    })
    scope_out = scope_result.get("project_blueprint")
    
    # 2 & 3. Finance and Risk (Parallel)
    import asyncio
    finance_graph = build_finance_subgraph()
    risk_graph = build_risk_subgraph()
    
    finance_result, risk_result = await asyncio.gather(
        finance_graph.ainvoke({
            "messages": [],
            "project_blueprint": scope_out,
            "validated_input": vi,
            "dev_cost_data": None,
            "infra_cost_data": None,
            "cost_estimate": None
        }),
        risk_graph.ainvoke({
            "project_blueprint": scope_out,
            "validated_input": vi,
            "timeline_risks": None,
            "technical_risks": None,
            "security_risks": None,
            "risk_assessment": None
        })
    )
    finance_out = finance_result.get("cost_estimate")
    risk_out = risk_result.get("risk_assessment")
    
    return {
        "project_blueprint": scope_out,
        "cost_estimate": finance_out,
        "risk_assessment": risk_out
    }
