"""
Agent C (Technical Risk Validator) output schema.

Represents an assessment of technical feasibility and risks
for a given project blueprint.
"""

from pydantic import BaseModel, Field


class Risk(BaseModel):
    """A specific risk identified in the project."""

    description: str = Field(
        description="Clear description of the risk."
    )
    severity: str = Field(
        description=(
            "Severity of the risk. "
            "Values: 'low', 'medium', 'high', 'critical'."
        )
    )
    affected_features: list[str] = Field(
        description="Names of the features impacted by this risk."
    )
    mitigation: str = Field(
        description="Suggested action to mitigate or manage the risk."
    )
    alternative_approach: str = Field(
        description="Alternative technical approach to avoid the risk entirely."
    )


class RiskAssessment(BaseModel):
    """
    Output of Agent C (Technical Risk Validator).
    
    Evaluates whether the proposed architecture, features, and timeline
    are technically feasible and identifies risks.
    """

    overall_risk_level: str = Field(
        description=(
            "The overall risk level of the project. "
            "Values: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'."
        )
    )
    quantitative_score: int = Field(
        description="Overall quantitative risk score (0-100, where 100 is maximum risk).",
        ge=0,
        le=100,
        default=0
    )
    budget_risk_score: int = Field(description="Budget risk score (0-100).", ge=0, le=100, default=0)
    technical_risk_score: int = Field(description="Technical risk score (0-100).", ge=0, le=100, default=0)
    timeline_risk_score: int = Field(description="Timeline risk score (0-100).", ge=0, le=100, default=0)
    security_risk_score: int = Field(description="Security risk score (0-100).", ge=0, le=100, default=0)
    confidence_score: int = Field(
        description="Confidence level in the risk assessment (0-100).",
        ge=0,
        le=100,
        default=85
    )
    feasibility_verdict: str = Field(
        description=(
            "Verdict on project feasibility. "
            "Values: 'FEASIBLE', 'RISKY', or 'INFEASIBLE'."
        )
    )
    risks: list[Risk] = Field(
        default_factory=list,
        description="List of identified risks."
    )
    infeasible_items: list[str] = Field(
        default_factory=list,
        description=(
            "Specific items (features, tech choices, timelines) that are "
            "considered completely infeasible. Example: '3-week timeline "
            "for SAP ERP migration'."
        )
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions made during the risk assessment."
    )
