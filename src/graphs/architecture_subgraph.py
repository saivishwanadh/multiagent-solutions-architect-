import os
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from src.schemas.validated_input import ValidatedInput
from src.schemas.blueprint import ProjectBlueprint, TechStack
from src.schemas.architecture import ArchitecturePattern, InfrastructurePlan, ArchitectureSummary
from src.schemas.conflict_feedback import ConflictFeedback
from src.config.settings import get_llm

class ArchitectureState(TypedDict):
    project_blueprint: ProjectBlueprint | None
    validated_input: ValidatedInput
    conflict_feedback: ConflictFeedback | None
    selected_stack: TechStack | None
    pattern: ArchitecturePattern | None
    infra_plan: InfrastructurePlan | None
    architecture_summary: ArchitectureSummary | None

def _read_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "config", "prompts", "architecture", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

async def node_tech_stack_selector(state: ArchitectureState) -> ArchitectureState:
    llm = get_llm(temperature=0.0).with_structured_output(TechStack)
    sys_prompt = _read_prompt("tech_stack_selector.txt")
    
    features_json = [f.model_dump_json() for f in (state["project_blueprint"].features if state["project_blueprint"] else [])]
    content = f"Project Type: {state['validated_input'].project_type}\n"
    content += f"Tech Preferences: {state['validated_input'].constraints.tech_preferences}\n"
    content += f"Features:\n{features_json}"
    
    if state.get("conflict_feedback"):
        cf = state["conflict_feedback"]
        content += f"\n\nCRITICAL OPTIMIZATION NEEDED (Iteration {cf.iteration_number}/1):\n"
        content += f"Guidance: {cf.guidance}\n"
        for vc in cf.violated_constraints:
            content += f"  - Violated: {vc.constraint_type} (target={vc.target_value}, current={vc.current_value})\n"
        content += "You MUST pick cheaper, lighter-weight technologies to reduce costs.\n"
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": content}
    ]
    stack = await llm.ainvoke(messages)
    state["selected_stack"] = stack
    return state

async def node_architecture_pattern(state: ArchitectureState) -> ArchitectureState:
    llm = get_llm(temperature=0.0).with_structured_output(ArchitecturePattern)
    sys_prompt = _read_prompt("architecture_pattern.txt")
    
    features_json = [f.model_dump_json() for f in (state["project_blueprint"].features if state["project_blueprint"] else [])]
    content = f"Tech Stack:\n{state['selected_stack'].model_dump_json()}\n"
    content += f"Features:\n{features_json}"
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": content}
    ]
    pattern = await llm.ainvoke(messages)
    state["pattern"] = pattern
    return state

async def node_infra_planner(state: ArchitectureState) -> ArchitectureState:
    llm = get_llm(temperature=0.0).with_structured_output(InfrastructurePlan)
    sys_prompt = _read_prompt("infra_planner.txt")
    
    content = f"Constraints:\n{state['validated_input'].constraints.model_dump_json()}\n"
    content += f"Tech Stack:\n{state['selected_stack'].model_dump_json()}\n"
    content += f"Architecture Pattern:\n{state['pattern'].model_dump_json()}\n"
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": content}
    ]
    infra = await llm.ainvoke(messages)
    state["infra_plan"] = infra
    return state

async def node_architecture_summary(state: ArchitectureState) -> ArchitectureState:
    summary = ArchitectureSummary(
        tech_stack=state["selected_stack"],
        architecture_pattern=state["pattern"],
        infrastructure_plan=state["infra_plan"],
        assumptions=state["infra_plan"].assumptions if state["infra_plan"] else [],
        alternatives_considered=state["infra_plan"].alternatives_considered if state["infra_plan"] else [],
        confidence_score=85
    )
    state["architecture_summary"] = summary
    if state["project_blueprint"]:
        state["project_blueprint"].tech_stack = state["selected_stack"]
    return state

def build_architecture_subgraph():
    graph = StateGraph(ArchitectureState)
    
    graph.add_node("tech_stack_selector", node_tech_stack_selector)
    graph.add_node("architecture_pattern", node_architecture_pattern)
    graph.add_node("infra_planner", node_infra_planner)
    graph.add_node("architecture_summary", node_architecture_summary)
    
    graph.add_edge(START, "tech_stack_selector")
    graph.add_edge("tech_stack_selector", "architecture_pattern")
    graph.add_edge("architecture_pattern", "infra_planner")
    graph.add_edge("infra_planner", "architecture_summary")
    graph.add_edge("architecture_summary", END)
    
    return graph.compile()

if __name__ == "__main__":
    from src.agents.guardrails import process_input
    from src.schemas.blueprint import ProjectBlueprint, Feature
    
    print("Testing Architecture Sub-graph Standalone...")
    vi = process_input("Build a secure medical patient portal. Budget $50k.")
    
    bp = ProjectBlueprint(
        project_name="Patient Portal",
        project_type="Web App",
        features=[
            Feature(name="Patient Login", description="Secure auth", priority=1, complexity="medium", category="security"),
            Feature(name="Medical Records", description="View records", priority=1, complexity="high", category="core")
        ],
        tech_stack=TechStack(backend="TBD", database="TBD", infrastructure="TBD"),
        milestones=[]
    )
    
    arch_graph = build_architecture_subgraph()
    result = arch_graph.invoke({
        "validated_input": vi,
        "project_blueprint": bp,
        "conflict_feedback": None,
        "selected_stack": None,
        "pattern": None,
        "infra_plan": None,
        "architecture_summary": None
    })
    
    summary = result["architecture_summary"]
    print(f"\nArchitecture Pattern: {summary.architecture_pattern.name}")
    print(f"Hosting: {summary.infrastructure_plan.hosting}")
    print(f"Frontend: {summary.tech_stack.frontend.name if summary.tech_stack.frontend else 'N/A'}")
    print(f"Database: {summary.tech_stack.database.name}")
