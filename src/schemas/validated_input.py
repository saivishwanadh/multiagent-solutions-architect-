"""
Agent 0 (Input Guardrails) output schema.

Represents the validated and classified user input.
This is the first structured data produced in the pipeline
and drives all downstream routing decisions.
"""

from typing import Literal
from pydantic import BaseModel, Field


class ExplicitConstraints(BaseModel):
    """Constraints explicitly stated by the user in their prompt."""

    budget: float | None = Field(
        default=None,
        description="Total budget in USD, if the user stated one."
    )
    timeline_weeks: int | None = Field(
        default=None,
        description="Desired timeline in weeks, if the user stated one."
    )
    tech_preferences: list[str] = Field(
        default_factory=list,
        description=(
            "Technologies the user explicitly wants or mentioned. "
            "Examples: 'SAP', 'Salesforce', 'React', 'Python', 'AWS', "
            "'on-premise', 'Kubernetes', 'PostgreSQL'."
        ),
    )
    compliance_needs: list[str] = Field(
        default_factory=list,
        description=(
            "Regulatory or compliance requirements mentioned. "
            "Examples: 'HIPAA', 'GDPR', 'SOC2', 'PCI-DSS', 'ISO 27001'."
        ),
    )
    deployment_model: str | None = Field(
        default=None,
        description=(
            "Where the system should be deployed. "
            "Values: 'cloud', 'on-premise', 'hybrid', or None if unspecified."
        ),
    )
    team_size: int | None = Field(
        default=None,
        description="Number of team members the user has available, if stated."
    )
    industry: str | None = Field(
        default=None,
        description=(
            "Industry or domain the project targets. "
            "Examples: 'healthcare', 'finance', 'retail', 'manufacturing', "
            "'logistics', 'education'."
        ),
    )
    expected_users: int | None = Field(
        default=None, 
        description="Total expected users, if stated."
    )
    concurrent_users: int | None = Field(
        default=None, 
        description="Expected concurrent users, if stated."
    )
    data_sensitivity: str | None = Field(
        default=None, 
        description="Sensitivity of data (e.g., 'PII', 'banking', 'public')."
    )
    sla_requirements: str | None = Field(
        default=None, 
        description="Service Level Agreement requirements (e.g., '99.99% uptime', '2s latency')."
    )


class ValidatedInput(BaseModel):
    """
    Output of Agent 0 (Input Guardrails).

    Validates whether the user prompt is a legitimate project query,
    classifies it into one of 6 categories, and extracts any
    explicit constraints.
    """

    is_valid: bool = Field(
        description=(
            "True if the prompt is a valid software/technology project query. "
            "False for off-topic, nonsensical, or non-project inputs."
        )
    )
    rejection_reason: str | None = Field(
        default=None,
        description="Why the input was rejected, if is_valid is False."
    )
    query_category: int = Field(
        description=(
            "The category of the query (1-6): "
            "1 = Feasibility ('Can we do this?'), "
            "2 = Architecture Recommendation ('How should we build it?'), "
            "3 = Resource & Timeline Estimation ('What will it take?'), "
            "4 = Trade-off / What-If Analysis, "
            "5 = Scope Modification / Change Request ('Pivot'), "
            "6 = General Q&A / Clarification about the current project."
        ),
        ge=1,
        le=6,
    )
    execution_intent: Literal["new_project", "update_proposal", "follow_up", "what_if"] = Field(
        default="new_project",
        description=(
            "The execution intent of the prompt: "
            "'new_project' for starting from scratch, "
            "'update_proposal' for changing constraints or pivoting an existing proposal, "
            "'follow_up' for asking questions about the existing proposal, "
            "'what_if' for scenario comparisons."
        )
    )
    project_type: str = Field(
        default="general",
        description=(
            "The broad type of project. "
            "Examples: 'ai_ml', 'web_application', 'mobile_app', "
            "'erp_implementation', 'system_integration', 'data_pipeline', "
            "'cloud_migration', 'iot', 'devops', 'api_development', "
            "'ecommerce', 'crm', 'custom_software', 'general'."
        ),
    )
    project_summary: str = Field(
        description=(
            "A clear, normalized 1-3 sentence summary of what "
            "the user is asking for."
        )
    )
    constraints: ExplicitConstraints = Field(
        default_factory=ExplicitConstraints,
        description="Constraints explicitly stated by the user."
    )
    missing_info: list[str] = Field(
        default_factory=list,
        description=(
            "Information the user did NOT provide but would be useful. "
            "Examples: 'No budget specified', 'No timeline given', "
            "'Deployment model unclear'."
        ),
    )
    detected_conflicts: list[str] = Field(
        default_factory=list,
        description=(
            "Obvious contradictions or tensions in the user's request. "
            "Example: 'User wants on-premise deployment in 2 weeks with "
            "$5,000 budget — these constraints conflict.'"
        ),
    )
    requires_document_generation: bool = Field(
        default=False,
        description="True if the user explicitly asked to save, generate, or download a document/file (e.g., .md file) in their prompt."
    )
