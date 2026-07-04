"""
Agent B (Financial Estimator) output schema.

Represents the cost and timeline estimations for the project blueprint.
Designed to handle software development, infrastructure, licensing,
and API costs for any project type.
"""

from pydantic import BaseModel, Field


class CostBreakdown(BaseModel):
    """Breakdown of total cost into specific categories."""

    infrastructure: dict[str, float] = Field(
        default_factory=dict,
        description="Detailed breakdown of infrastructure & hosting costs (e.g. {'GPU Cluster': 120000, 'Storage': 45000, 'Misc': 16832})."
    )
    managed_services_and_apis: float = Field(
        default=0.0,
        description="Estimated costs for managed services and APIs (e.g., OpenAI, AWS API Gateway, ERP connectors)."
    )
    development_cost: float = Field(
        default=0.0,
        description="Estimated labor cost for engineering and development."
    )
    third_party: float = Field(
        default=0.0,
        description="Third-party services, tools, or integrations (e.g., Stripe, Twilio)."
    )
    licensing: float = Field(
        default=0.0,
        description="Software licensing fees (e.g., SAP, Salesforce, proprietary tools)."
    )


class FeatureCost(BaseModel):
    """Estimated cost for a single feature."""

    feature_name: str = Field(description="Name of the feature.")
    estimated_cost: float = Field(description="Estimated cost in USD.")


class CostEstimate(BaseModel):
    """
    Output of Agent B (Financial Estimator).
    
    Contains overall timeline, cost breakdowns, and a verdict on
    whether the project meets the user's budget constraints.
    """

    total_estimated_cost: float = Field(
        description="Total estimated cost for the project in USD."
    )
    confidence_score: int = Field(
        description="Confidence level in the cost estimates (0-100).",
        ge=0,
        le=100,
        default=85
    )
    cost_breakdown: CostBreakdown = Field(
        description="Detailed breakdown of the total cost."
    )
    timeline_weeks: int = Field(
        description="Estimated total timeline in weeks."
    )
    team_size: int = Field(
        description="Recommended number of team members."
    )
    budget_verdict: str = Field(
        description=(
            "Verdict on whether the estimate meets the budget. "
            "Values: 'PASS' (within budget) or 'OVER_BUDGET' (exceeds budget)."
        )
    )
    budget_delta: float = Field(
        description=(
            "Difference between total estimated cost and user budget. "
            "Positive means over budget, negative means under budget."
        )
    )
    user_budget: float | None = Field(
        default=None,
        description="The budget constraint provided by the user, if any."
    )
    cost_per_feature: list[FeatureCost] = Field(
        description="Breakdown of costs mapped to specific features."
    )
    cost_saving_suggestions: list[str] = Field(
        default_factory=list,
        description=(
            "Actionable suggestions to reduce cost. "
            "Example: 'Use open-source PostgreSQL instead of Oracle', "
            "'Defer analytics dashboard to Phase 2'."
        )
    )
