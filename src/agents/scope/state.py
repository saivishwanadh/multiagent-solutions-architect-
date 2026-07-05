from typing import Any, TypedDict
from pydantic import BaseModel
from src.schemas.validated_input import ValidatedInput
from src.schemas.conflict_feedback import ConflictFeedback
from src.schemas.blueprint import ProjectBlueprint, Feature, Milestone, TechStack, ArchitecturePattern, InfrastructurePlan

class ScopeState(TypedDict):
    messages: list[Any]
    validated_input: ValidatedInput | None
    initial_user_prompt: str | None
    latest_user_prompt: str | None
    negotiation_history: list[dict]
    previous_final_output: Any | None
    conflict_feedback: ConflictFeedback | None
    
    parsed_requirements: str | None
    features: list[Feature] | None
    architecture_design: Any | None
    milestones: list[Milestone] | None
    project_blueprint: ProjectBlueprint | None
    coverage_feedback: str | None

class FeatureList(BaseModel):
    features: list[Feature]

class MilestoneList(BaseModel):
    milestones: list[Milestone]

class ArchitectureDesign(BaseModel):
    tech_stack: TechStack
    architecture_pattern: ArchitecturePattern
    infrastructure_plan: InfrastructurePlan
    alternatives_considered: list[str]
