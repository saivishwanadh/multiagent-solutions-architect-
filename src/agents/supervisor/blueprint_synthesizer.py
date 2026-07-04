"""
Agent S (Blueprint Synthesizer).

Takes the raw outputs from Agent A (Scope), Agent B (Financials), 
and Agent C (Risks) and compiles them into a polished FinalBlueprint.
"""

from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from src.config.settings import get_llm
from src.schemas.blueprint import ProjectBlueprint
from src.schemas.cost_estimate import CostEstimate
from src.schemas.risk_assessment import RiskAssessment
from src.schemas.risk_assessment import RiskAssessment
from src.schemas.final_blueprint import FinalBlueprint
from src.tools.file_tools import save_document

# Paths
PROMPT_PATH = Path(__file__).parent.parent.parent / "config" / "prompts" / "blueprint_synthesizer.txt"


def load_system_prompt() -> str:
    """Loads the system prompt from the configuration file."""
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _build_user_message(
    blueprint: ProjectBlueprint,
    cost_estimate: CostEstimate,
    risk_assessment: RiskAssessment,
    user_prompt: str | None = None,
) -> str:
    """
    Constructs the user message sent to the LLM.
    Aggregates the data from all three previous agents.
    """
    parts = []

    if user_prompt:
        parts.append(f"USER'S LATEST QUERY/FOLLOW-UP: {user_prompt}")
        parts.append("INSTRUCTION: If the user asked a question, explicitly answer it in the first paragraph of the executive summary.\n")


    parts.append("=========================================")
    parts.append("1. SCOPE (from Agent A)")
    parts.append("=========================================")
    parts.append(f"PROJECT NAME: {blueprint.project_name}")
    parts.append(f"PROJECT TYPE: {blueprint.project_type}")
    
    parts.append("\nFEATURES:")
    for f in blueprint.features:
        parts.append(f"  - [{f.priority}] {f.name} ({f.complexity})")
    
    parts.append("\nTECH STACK:")
    parts.append(f"  Backend: {blueprint.tech_stack.backend}")
    parts.append(f"  Database: {blueprint.tech_stack.database}")
    parts.append(f"  Infrastructure: {blueprint.tech_stack.infrastructure}")
    if blueprint.tech_stack.frontend:
        parts.append(f"  Frontend: {blueprint.tech_stack.frontend}")
    if blueprint.tech_stack.enterprise_platforms:
        parts.append(f"  Enterprise Platforms: {', '.join(blueprint.tech_stack.enterprise_platforms)}")
    if blueprint.tech_stack.ai_models:
        parts.append(f"  AI Models: {', '.join(blueprint.tech_stack.ai_models)}")
    if blueprint.tech_stack.integrations:
        parts.append(f"  Integrations: {', '.join(blueprint.tech_stack.integrations)}")

    parts.append("\nMILESTONES:")
    for m in blueprint.milestones:
        parts.append(f"  - {m.order}. {m.name}")

    parts.append("\n=========================================")
    parts.append("2. FINANCIALS (from Agent B)")
    parts.append("=========================================")
    parts.append(f"TOTAL COST: ${cost_estimate.total_estimated_cost:,.0f}")
    parts.append(f"TIMELINE: {cost_estimate.timeline_weeks} weeks")
    parts.append(f"TEAM SIZE: {cost_estimate.team_size}")
    parts.append(f"BUDGET VERDICT: {cost_estimate.budget_verdict} (Delta: ${cost_estimate.budget_delta:,.0f})")
    
    parts.append("\nCOST BREAKDOWN:")
    parts.append(f"  Infrastructure: ${cost_estimate.cost_breakdown.infrastructure:,.0f}")
    parts.append(f"  Managed Services: ${cost_estimate.cost_breakdown.managed_services_and_apis:,.0f}")
    parts.append(f"  Development: ${cost_estimate.cost_breakdown.development_cost:,.0f}")
    parts.append(f"  Third Party: ${cost_estimate.cost_breakdown.third_party:,.0f}")
    parts.append(f"  Licensing: ${cost_estimate.cost_breakdown.licensing:,.0f}")

    if cost_estimate.cost_saving_suggestions:
        parts.append("\nCOST SAVING SUGGESTIONS:")
        for s in cost_estimate.cost_saving_suggestions:
            parts.append(f"  - {s}")

    parts.append("\n=========================================")
    parts.append("3. RISKS (from Agent C)")
    parts.append("=========================================")
    parts.append(f"OVERALL RISK LEVEL: {risk_assessment.overall_risk_level}")
    parts.append(f"FEASIBILITY VERDICT: {risk_assessment.feasibility_verdict}")
    
    parts.append("\nIDENTIFIED RISKS:")
    for r in risk_assessment.risks:
        parts.append(f"  - [{r.severity.upper()}] {r.description}")
        parts.append(f"    Mitigation: {r.mitigation}")
    
    if risk_assessment.infeasible_items:
        parts.append("\nINFEASIBLE ITEMS:")
        for item in risk_assessment.infeasible_items:
            parts.append(f"  - {item}")

    # Combine assumptions
    all_assumptions = list(blueprint.assumptions)
    if risk_assessment.assumptions:
        all_assumptions.extend(risk_assessment.assumptions)
    
    if all_assumptions:
        parts.append("\n=========================================")
        parts.append("4. CONSOLIDATED ASSUMPTIONS")
        parts.append("=========================================")
        for a in all_assumptions:
            parts.append(f"  - {a}")

    return "\n".join(parts)


def get_blueprint_synthesizer_agent():
    """
    Constructs the synthesizer agent pipeline.
    Uses LCEL to chain prompt -> LLM -> structured output.
    """
    system_prompt = load_system_prompt()

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{user_message}"),
    ])

    # Slight temperature to allow for good executive summary writing
    llm = get_llm(temperature=0.4) 
    structured_llm = llm.with_structured_output(FinalBlueprint)

    chain = prompt_template | structured_llm
    return chain


async def process_synthesis(
    blueprint: ProjectBlueprint,
    cost_estimate: CostEstimate,
    risk_assessment: RiskAssessment,
    user_prompt: str | None = None,
) -> FinalBlueprint:
    """
    Runs the blueprint synthesizer agent.

    Args:
        blueprint: The final scope from Agent A.
        cost_estimate: The financials from Agent B.
        risk_assessment: The risk profile from Agent C.

    Returns:
        A FinalBlueprint ready for presentation.
    """
    agent = get_blueprint_synthesizer_agent()
    user_message = _build_user_message(blueprint, cost_estimate, risk_assessment, user_prompt)
    result = await agent.ainvoke({"user_message": user_message})
    
    # Overwrite the LLM's hallucination of these fields to guarantee 
    # data integrity from the previous agents. We only want the LLM 
    # for the text synthesis (summary, recommendations, etc.).
    result.features = blueprint.features
    result.tech_stack = blueprint.tech_stack
    result.milestones = blueprint.milestones
    result.total_cost = cost_estimate.total_estimated_cost
    result.cost_breakdown = cost_estimate.cost_breakdown
    result.timeline_weeks = cost_estimate.timeline_weeks
    result.team_size = cost_estimate.team_size
    
    return result

def _format_markdown(blueprint: FinalBlueprint) -> str:
    """Formats the FinalBlueprint into a clean Markdown string."""
    md = f"# Project Proposal: {blueprint.project_name}\n\n"
    md += f"## Executive Summary\n{blueprint.executive_summary}\n\n"
    md += f"**Budget Status**: {blueprint.budget_status}\n"
    md += f"**Feasibility Verdict**: {blueprint.feasibility_verdict}\n"
    md += f"**Overall Risk**: {blueprint.overall_risk}\n\n"
    
    md += f"## Financials & Timeline\n"
    md += f"- **Total Cost**: ${blueprint.total_cost:,.0f}\n"
    md += f"- **Timeline**: {blueprint.timeline_weeks} weeks\n"
    md += f"- **Team Size**: {blueprint.team_size}\n\n"
    
    if blueprint.cost_breakdown:
        md += f"### Cost Breakdown\n"
        md += f"- Infrastructure: ${blueprint.cost_breakdown.infrastructure:,.0f}\n"
        md += f"- Managed Services: ${blueprint.cost_breakdown.managed_services_and_apis:,.0f}\n"
        md += f"- Development: ${blueprint.cost_breakdown.development_cost:,.0f}\n"
        md += f"- Third Party: ${blueprint.cost_breakdown.third_party:,.0f}\n"
        md += f"- Licensing: ${blueprint.cost_breakdown.licensing:,.0f}\n\n"
    
    md += f"## Technical Architecture\n"
    md += f"- **Backend**: {blueprint.tech_stack.backend}\n"
    md += f"- **Database**: {blueprint.tech_stack.database}\n"
    md += f"- **Infrastructure**: {blueprint.tech_stack.infrastructure}\n"
    if blueprint.tech_stack.frontend:
        md += f"- **Frontend**: {blueprint.tech_stack.frontend}\n"
    
    md += f"\n## Key Features\n"
    for f in blueprint.features:
        md += f"- **{f.name}** ({f.priority}, {f.complexity})\n"
        
    md += f"\n## Implementation Milestones\n"
    for m in blueprint.milestones:
        md += f"- **Phase {m.order}**: {m.name}\n"
        
    md += f"\n## Top Risks & Mitigations\n"
    for r in blueprint.top_risks:
        md += f"- **{r.severity.upper()}**: {r.description}\n  - *Mitigation*: {r.mitigation}\n"
        
    md += f"\n## Strategic Recommendations\n"
    for rec in blueprint.recommendations:
        md += f"- {rec}\n"
        
    return md


async def node_proposal_generator(state: dict) -> dict:
    """Uses Agent S to produce the final output."""
    
    # If this is a direct_qa routing, the sub-graphs were skipped, so we restore from previous
    if not state.get("scope_output") and state.get("previous_final_output"):
        prev = state["previous_final_output"]
        state["scope_output"] = prev
        from src.schemas.blueprint import ProjectBlueprint
        from src.schemas.cost_estimate import CostEstimate
        from src.schemas.risk_assessment import RiskAssessment
        
        state["scope_output"] = ProjectBlueprint(
            project_name=prev.project_name,
            project_type="Unknown",
            features=prev.features,
            tech_stack=prev.tech_stack,
            milestones=prev.milestones,
            assumptions=prev.assumptions
        )
        state["architecture_output"] = None 
        state["cost_estimate"] = CostEstimate(
            total_estimated_cost=prev.total_cost,
            cost_breakdown=prev.cost_breakdown,
            timeline_weeks=prev.timeline_weeks,
            team_size=prev.team_size,
            cost_saving_suggestions=[],
            budget_verdict=prev.budget_status,
            budget_delta=0,
            cost_per_feature=[],
            user_budget=None
        )
        state["risk_assessment"] = RiskAssessment(
            overall_risk_level=prev.overall_risk,
            feasibility_verdict=prev.feasibility_verdict,
            risks=prev.top_risks,
            infeasible_items=[],
            assumptions=[]
        )
    
    combined_blueprint = state.get("scope_output")
    arch = state.get("architecture_output")
    
    if combined_blueprint and arch:
        combined_blueprint.tech_stack = arch.tech_stack
    
    final = await process_synthesis(
        blueprint=combined_blueprint,
        cost_estimate=state.get("cost_estimate"),
        risk_assessment=state.get("risk_assessment"),
        user_prompt=state.get("user_prompt")
    )
    
    # Generate and physically save the markdown document
    markdown_content = _format_markdown(final)
    save_document(markdown_content)
    
    return {"final_output": final}
