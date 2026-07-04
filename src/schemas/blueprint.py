"""
Agent A (Scope Specialist) output schema.

Represents a structured project blueprint: features, tech stack,
and milestones. Works for any project type — AI/ML, ERP, web apps,
integrations, cloud migrations, etc.
"""

from typing import Literal
from pydantic import BaseModel, Field

class TechChoice(BaseModel):
    name: str = Field(description="Name of the technology.")
    rationale: str = Field(description="Why this technology was chosen.")

class ArchitecturePattern(BaseModel):
    name: str = Field(description="Name of the architecture pattern (e.g. Microservices, Monolith, Serverless).")
    rationale: str = Field(description="Why this pattern was chosen.")

class InfrastructurePlan(BaseModel):
    hosting: str = Field(description="Where the application will be hosted (e.g. AWS ECS, Vercel, On-Prem).")
    scaling_strategy: str = Field(description="How the system will scale (e.g. Auto-scaling groups, manual).")
    deployment_strategy: str = Field(description="How updates will be rolled out (e.g. Blue/Green, Rolling).")


class Feature(BaseModel):
    """A single feature or work item in the project."""

    name: str = Field(
        description="Short name of the feature. Example: 'User Authentication'."
    )
    description: str = Field(
        description="What this feature does and why it is needed."
    )
    priority: Literal["P0", "P1", "P2", "P3"] = Field(
        description=(
            "How essential this feature is. "
            "P0 = absolutely essential (system is useless without it), "
            "P1 = very important, "
            "P2 = important but could be deferred, "
            "P3 = nice-to-have / stretch goal."
        )
    )
    complexity: str = Field(
        description=(
            "Engineering complexity: 'low', 'medium', or 'high'. "
            "Low = straightforward, well-known patterns. "
            "Medium = requires some design decisions or integrations. "
            "High = significant R&D, complex integrations, or novel work."
        )
    )
    category: str = Field(
        default="core",
        description=(
            "Feature category. Examples: 'core', 'infrastructure', "
            "'integration', 'ui_ux', 'security', 'data', 'reporting', "
            "'devops', 'testing', 'compliance'."
        ),
    )


class TechStack(BaseModel):
    """The recommended technology stack for the project."""

    frontend: TechChoice | None = Field(
        default=None,
        description="Frontend framework or technology."
    )
    backend: TechChoice = Field(
        description="Backend language/framework."
    )
    database: TechChoice = Field(
        description="Primary database."
    )
    infrastructure: TechChoice = Field(
        description="Hosting and infrastructure."
    )
    enterprise_platforms: list[TechChoice] = Field(
        default_factory=list,
        description="Core enterprise platforms being implemented or customized."
    )
    ai_models: list[TechChoice] = Field(
        default_factory=list,
        description="AI/ML models or services used, if applicable."
    )
    integrations: list[TechChoice] = Field(
        default_factory=list,
        description="Third-party systems or APIs to integrate with."
    )
    other: list[TechChoice] = Field(
        default_factory=list,
        description="Additional tools, services, or technologies."
    )


class Milestone(BaseModel):
    """A project milestone grouping related features."""

    name: str = Field(
        description=(
            "Milestone name. "
            "Examples: 'MVP Launch', 'Phase 1 - Core Backend', "
            "'ERP Data Migration', 'Integration Testing'."
        )
    )
    features_included: list[str] = Field(
        description="Names of the features included in this milestone."
    )
    order: int = Field(
        description="Sequence order (1 = first milestone to deliver).",
        ge=1,
    )


class ProjectBlueprint(BaseModel):
    """
    Output of Agent A (Scope Specialist).

    A structured breakdown of the project into features,
    tech stack, and milestones. This is the central data
    structure that feeds into cost estimation and risk validation.
    The final output combining scope, tech stack, milestones, and architecture.
    """

    project_name: str = Field(description="A concise, catchy name for the project.")
    project_type: str = Field(description="e.g., 'Web App', 'Internal Tool', 'Mobile App', 'Data Pipeline'")
    features: list[Feature] = Field(description="List of features/work items.")
    tech_stack: TechStack = Field(description="The selected tech stack for the project.")
    architecture_pattern: ArchitecturePattern | None = Field(default=None, description="Architecture pattern.")
    infrastructure_plan: InfrastructurePlan | None = Field(default=None, description="Infrastructure plan.")
    milestones: list[Milestone] = Field(description="List of project milestones.")
    assumptions: list[str] = Field(
        default_factory=list,
        description=(
            "Assumptions made while parsing the requirements. "
            "Example: 'Assuming the client has existing AWS infrastructure.'"
        )
    )
    alternatives_considered: list[str] = Field(
        default_factory=list,
        description="Alternative technologies considered but rejected, and why. Example: 'Considered Pinecone, but chose Milvus for on-premise support.'"
    )
    confidence_score: int = Field(
        default=85,
        ge=0,
        le=100,
        description="Confidence level in the overall blueprint plan (0-100)."
    )
