import sys
sys.stdout.reconfigure(encoding='utf-8')
import uuid
import asyncio
import time
from src.graphs.supervisor import build_supervisor_graph
from src.schemas.state import SupervisorState
from langgraph.types import Command


# ─────────────────────────────────────────────────
#  Rich Markdown-Style Output Formatter
# ─────────────────────────────────────────────────

def print_full_proposal(final, iterations):
    """Prints the complete FinalBlueprint as a rich, readable report."""
    W = 72
    sep = "═" * W
    sub = "─" * W
    
    print(f"\n{sep}")
    print(f"  ENTERPRISE PROJECT PROPOSAL")
    print(f"{sep}")
    
    # ── Header & Metadata ──
    print(f"""
  Project:     {final.project_name}
  Proposal ID: {final.metadata.proposal_id} ({final.metadata.proposal_version})
  Generated:   {final.metadata.generated_time}
  Verdict:     {final.feasibility_verdict}
  Risk Level:  {final.overall_risk}
  Budget:      {final.budget_status}
  Total Cost:  ${final.total_cost:,.0f}
  Timeline:    {final.timeline_weeks} weeks
  Team Size:   {final.team_size} members
  Iterations:  {iterations}""")
    
    # ── Confidence Scores ──
    print(f"\n{sub}")
    print("  CONFIDENCE SCORES")
    print(f"{sub}")
    print(f"  Scope: {final.department_confidences.scope}% | Arch: {final.department_confidences.architecture}% | Finance: {final.department_confidences.finance}% | Risk: {final.department_confidences.risk}%")

    # ── Executive Summary ──
    print(f"\n{sub}")
    print("  EXECUTIVE SUMMARY")
    print(f"{sub}")
    es = final.executive_summary
    print(f"  [Objective]\n  {es.objective}\n")
    print(f"  [Architecture]\n  {es.architecture}\n")
    print(f"  [Cost & Timeline]\n  {es.cost}\n")
    print(f"  [Verdict Reasoning]\n  {es.verdict}\n")
    print(f"  [Final Recommendation]\n  {es.recommendation}")
    
    # ── Features ──
    print(f"\n{sub}")
    print(f"  FEATURES ({len(final.features)} total)")
    print(f"{sub}")
    for f in final.features:
        print(f"\n  [{f.priority}] {f.name}")
        print(f"     Complexity: {f.complexity.upper()}  |  Category: {f.category.upper()}")
        # Wrap description
        desc_lines = f.description.split('. ')
        for dl in desc_lines:
            dl = dl.strip()
            if dl:
                print(f"     {dl}{'.' if not dl.endswith('.') else ''}")
    
    # ── Tech Stack ──
    print(f"\n{sub}")
    print("  TECHNOLOGY STACK")
    print(f"{sub}")
    ts = final.tech_stack
    stack_items = [
        ("Backend", ts.backend),
        ("Database", ts.database),
        ("Infrastructure", ts.infrastructure),
    ]
    if ts.frontend:
        stack_items.append(("Frontend", ts.frontend))
    if ts.ai_models:
        for i, model in enumerate(ts.ai_models):
            stack_items.append((f"AI Model {i+1}", model))
    if ts.enterprise_platforms:
        for i, plat in enumerate(ts.enterprise_platforms):
            stack_items.append((f"Platform {i+1}", plat))
    if ts.integrations:
        for i, integ in enumerate(ts.integrations):
            stack_items.append((f"Integration {i+1}", integ))
    if ts.other:
        for i, oth in enumerate(ts.other):
            stack_items.append((f"Other {i+1}", oth))
    
    for label, choice in stack_items:
        print(f"\n  {label}: {choice.name}")
        print(f"    → Rationale: {choice.rationale}")
    
    # ── Cost Breakdown ──
    print(f"\n{sub}")
    print("  COST BREAKDOWN")
    print(f"{sub}")
    cb = final.cost_breakdown
    
    # Summarize infrastructure dict
    infra_total = sum(cb.infrastructure.values()) if isinstance(cb.infrastructure, dict) else 0.0
    
    cost_rows = [
        ("Development", cb.development_cost),
        ("Infrastructure", infra_total),
        ("Managed Services & APIs", cb.managed_services_and_apis),
        ("Third-Party Tools", cb.third_party),
        ("Licensing", cb.licensing),
    ]
    max_cost_label = max(len(r[0]) for r in cost_rows)
    for label, amount in cost_rows:
        print(f"  {label:<{max_cost_label + 2}} ${amount:>12,.0f}")
        # Print sub-categories for infrastructure
        if label == "Infrastructure" and isinstance(cb.infrastructure, dict):
            for sub_cat, sub_amt in cb.infrastructure.items():
                print(f"      ├─ {sub_cat:<{max_cost_label - 4}} ${sub_amt:>10,.0f}")
    
    print(f"  {'─' * (max_cost_label + 16)}")
    print(f"  {'TOTAL':<{max_cost_label + 2}} ${final.total_cost:>12,.0f}")
    
    # ── Milestones ──
    print(f"\n{sub}")
    print(f"  MILESTONES ({len(final.milestones)} phases)")
    print(f"{sub}")
    for m in sorted(final.milestones, key=lambda x: x.order):
        print(f"\n  Phase {m.order}: {m.name}")
        for feat in m.features_included:
            print(f"    ├─ {feat}")
    
    # ── Top Risks ──
    print(f"\n{sub}")
    print(f"  TOP RISKS ({len(final.top_risks)})")
    print(f"{sub}")
    for r in final.top_risks:
        print(f"\n  [{r.severity.upper()}] {r.description}")
        if r.mitigation:
            print(f"     → Mitigation: {r.mitigation}")
    
    # ── Recommendations ──
    print(f"\n{sub}")
    print("  PHASED RECOMMENDATIONS")
    print(f"{sub}")
    for i, rec in enumerate(final.phased_recommendations, 1):
        delta_str = f"-${abs(rec.cost_delta):,.0f}" if rec.cost_delta < 0 else f"+${rec.cost_delta:,.0f}"
        print(f"  [{rec.phase_name}] (Delta: {delta_str})")
        print(f"    → {rec.actionable_advice}")
    
    # ── Next Steps ──
    print(f"\n{sub}")
    print("  NEXT STEPS")
    print(f"{sub}")
    for i, step in enumerate(final.next_steps, 1):
        print(f"  {i}. {step}")
    
    # ── Assumptions ──
    if final.assumptions:
        print(f"\n{sub}")
        print("  ASSUMPTIONS")
        print(f"{sub}")
        for a in final.assumptions:
            print(f"  • {a}")
    
    print(f"\n{sep}")
    print(f"  END OF PROPOSAL")
    print(f"{sep}\n")


# ─────────────────────────────────────────────────
#  Streaming Event Printer
# ─────────────────────────────────────────────────

# Map internal node names to user-friendly labels
NODE_LABELS = {
    "load_memory": "Loading organizational memory",
    "reset_state": "Preparing workspace",
    "intake_analyzer": "Validating & classifying your request",
    "invoke_scope": "Scope Specialist — extracting features & milestones",
    "invoke_architecture": "Architecture Agent — selecting tech stack & patterns",
    "invoke_finance": "Finance Agent — estimating costs",
    "invoke_risk": "Risk Validator — analyzing feasibility",
    "invoke_finance_and_risk": "Finance + Risk (running in parallel)",
    "result_aggregator": "Aggregating results",
    "constraint_validator": "Checking budget & timeline constraints",
    "optimization_router": "Optimization — finding cost reductions",
    "generate_feedback": "Generating refinement guidance",
    "compute_delta": "Computing changes from previous proposal",
    "proposal_generator": "Synthesizing final proposal",
    "clarification": "Awaiting user clarification",
    "scenario_splitter": "Splitting trade-off scenarios",
    "scenario_comparator": "Comparing scenarios",
    "hitl_handler": "Human-in-the-loop decision needed",
}

def print_node_status(node_name: str, elapsed: float):
    """Prints a user-friendly status line when a node completes."""
    label = NODE_LABELS.get(node_name, f"  {node_name}")
    print(f"  ✓ {label} ({elapsed:.1f}s)")


# ─────────────────────────────────────────────────
#  Main Interactive Loop with Streaming
# ─────────────────────────────────────────────────

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import os

async def interactive_loop():
    print("═" * 56)
    print("  Multi-Agent Enterprise Solutions Architect")
    print("  Powered by LangGraph + Gemini")
    print("═" * 56)
    print("  Type 'exit' or 'quit' to stop.\n")
    
    # Generate a unique thread ID for persistent session
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    print(f"  Session ID: {thread_id[:8]}...\n")

    import aiosqlite
    db_path = os.path.join(os.path.dirname(__file__), "memory.db")
    
    # Custom connection with WAL mode and high timeout to prevent locks during parallel execution
    async with aiosqlite.connect(db_path, timeout=30.0) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("PRAGMA synchronous=NORMAL;")
        
        checkpointer = AsyncSqliteSaver(conn)
        await checkpointer.setup()
        
        # Build the graph and compile with the connected checkpointer
        from src.graphs.supervisor import build_supervisor_graph
        app = build_supervisor_graph().compile(checkpointer=checkpointer)

        while True:
            try:
                user_input = input("\n📎 Enter your project request: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Exiting...")
                break

            print(f"\n{'─' * 56}")
            print(f"  Starting pipeline...")
            print(f"{'─' * 56}")
            
            start_time = time.time()
            node_start = time.time()
            
            # Stream the execution — shows real-time progress per node
            async for event in app.astream({"user_prompt": user_input}, config):
                now = time.time()
                for node_name in event:
                    elapsed = now - node_start
                    print_node_status(node_name, elapsed)
                    node_start = now
            
            total_time = time.time() - start_time
            
            final_state = (await app.aget_state(config)).values
            
            # Handle Human-in-the-Loop interrupts
            graph_state = await app.aget_state(config)
            while graph_state.next:
                if "clarification" in graph_state.next:
                    print("\n  The system needs clarification on missing constraints (e.g. Budget, Timeline).")
                    choice = input("  Please provide the missing info: ").strip()
                    node_start = time.time()
                    async for event in app.astream(Command(resume=choice), config):
                        now = time.time()
                        for node_name in event:
                            print_node_status(node_name, now - node_start)
                            node_start = now
                    final_state = (await app.aget_state(config)).values
                else:
                    interrupt_data = None
                    if graph_state.tasks and graph_state.tasks[0].interrupts:
                        payload = graph_state.tasks[0].interrupts[0].value
                        if isinstance(payload, dict) and "options" in payload:
                            interrupt_data = payload["options"]
                    
                    if not interrupt_data:
                        interrupt_data = graph_state.values.get("deadlock_options") or []

                    print("\n  The agents have deadlocked and need your input:")
                    for i, opt in enumerate(interrupt_data):
                        desc = opt.get('description', opt) if isinstance(opt, dict) else opt
                        print(f"    Option {chr(65+i)}: {desc}")
                    
                    choice = input("\n  Pick an option (e.g. A, B, C): ").strip()
                    print(f"\n  Resuming with choice '{choice}'...\n")
                    node_start = time.time()
                    async for event in app.astream(Command(resume=choice), config):
                        now = time.time()
                        for node_name in event:
                            print_node_status(node_name, now - node_start)
                            node_start = now
                    final_state = (await app.aget_state(config)).values
                
                graph_state = await app.aget_state(config)
            
            vi = final_state.get("validated_input")
            if vi and not vi.is_valid:
                print(f"\n  Request blocked: {vi.rejection_reason}")
                continue
            
            print(f"\n{'─' * 56}")
            print(f"  Pipeline completed in {total_time:.1f}s")
            print(f"{'─' * 56}")
            
            comp = final_state.get("scenario_comparison")
            delta = final_state.get("delta_summary")
            final = final_state.get("final_output")
            qa = final_state.get("qa_response")
            
            if qa:
                print(f"\n  Agent Response:\n\n{qa}\n")
                await app.aupdate_state(config, {"qa_response": None})
            
            elif comp:
                print("\n═══ TRADEOFF ANALYSIS ═══")
                print(f"Scenario A:\n  Cost: ${comp.scenario_a.total_cost:,.0f}\n  Risk: {comp.scenario_a.risk_level}\n  Pros: {', '.join(comp.scenario_a.pros)}")
                print(f"\nScenario B:\n  Cost: ${comp.scenario_b.total_cost:,.0f}\n  Risk: {comp.scenario_b.risk_level}\n  Pros: {', '.join(comp.scenario_b.pros)}")
                print(f"\nRecommendation: {comp.recommendation}")
                await app.aupdate_state(config, {"scenario_comparison": None})
            
            elif delta:
                print(f"\n{'─' * 56}")
                print(f"  {delta}")
                print(f"{'─' * 56}")
                if final:
                    print(f"\n  Updated Cost: ${final.total_cost:,.0f}  |  Risk: {final.overall_risk}")
                    print(f"\n{final.executive_summary}")
                await app.aupdate_state(config, {"delta_summary": None})
                
            elif final:
                print_full_proposal(final, final_state.get('conflict_loop_count', 0))
            else:
                print("  No final output generated. (Pipeline may have been rejected or aborted)")

if __name__ == "__main__":
    asyncio.run(interactive_loop())
