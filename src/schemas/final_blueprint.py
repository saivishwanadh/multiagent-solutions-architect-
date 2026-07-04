"""
Agent S (Blueprint Synthesizer) output schema.

Represents the final, polished output presented to the user.
Combines scope, financials, risks, and recommendations into a cohesive document.
"""

from pydantic import BaseModel, Field
from src.schemas.blueprint import Feature, TechStack, Milestone
from src.schemas.cost_estimate import CostBreakdown
from src.schemas.risk_assessment import Risk

class ExecutiveSummary(BaseModel):
    objective: str = Field(description="The primary objective of the project.")
    architecture: str = Field(description="High-level architecture overview.")
    cost: str = Field(description="High-level cost summary.")
    verdict: str = Field(description="The verdict reasoning.")
    recommendation: str = Field(description="Final recommendation for the CEO.")

class ProposalMetadata(BaseModel):
    proposal_version: str = Field(description="Version string, e.g., 'v1.0'.")
    generated_time: str = Field(description="ISO 8601 timestamp.")
    proposal_id: str = Field(description="Unique identifier for this proposal.")

class DepartmentConfidence(BaseModel):
    scope: int = Field(description="Scope confidence (0-100).")
    architecture: int = Field(description="Architecture confidence (0-100).")
    finance: int = Field(description="Finance confidence (0-100).")
    risk: int = Field(description="Risk confidence (0-100).")

class PhasedRecommendation(BaseModel):
    phase_name: str = Field(description="Name of the phase, e.g., 'Phase 1 MVP'.")
    actionable_advice: str = Field(description="What specific features to defer or actions to take.")
    cost_delta: float = Field(description="The approximate cost savings or addition for this phase.")


class FinalBlueprint(BaseModel):
    """
    Output of Agent S (Blueprint Synthesizer).
    
    The comprehensive final project proposal and analysis.
    """

    metadata: ProposalMetadata = Field(
        description="Metadata for versioning and auditing."
    )
    department_confidences: DepartmentConfidence = Field(
        description="Confidence scores from each department."
    )
    executive_summary: ExecutiveSummary = Field(
        description="A structured, one-page executive summary."
    )
    feasibility_verdict: str = Field(
        description=(
            "Final GO/NO-GO decision. "
            "Values: 'GO', 'GO_WITH_CAVEATS', or 'NO_GO'."
        )
    )
    project_name: str = Field(description="Name of the project.")
    features: list[Feature] = Field(description="Final list of approved features.")
    tech_stack: TechStack = Field(description="Final recommended tech stack.")
    
    # Financials
    total_cost: float = Field(description="Total estimated cost.")
    cost_breakdown: CostBreakdown = Field(description="Cost breakdown.")
    budget_status: str = Field(
        description="Budget verdict (e.g., 'Within Budget', 'Exceeds by $5,000')."
    )
    
    # Timeline & Resources
    timeline_weeks: int = Field(description="Total estimated timeline in weeks.")
    team_size: int = Field(description="Recommended team size.")
    milestones: list[Milestone] = Field(description="Project milestones.")
    
    # Risks
    overall_risk: str = Field(description="Overall risk level (LOW/MEDIUM/HIGH/CRITICAL).")
    top_risks: list[Risk] = Field(description="The most critical risks to monitor.")
    
    # Guidance
    phased_recommendations: list[PhasedRecommendation] = Field(
        description="Actionable, phased recommendations with cost delta approximations."
    )
    next_steps: list[str] = Field(
        description="Concrete next steps to initiate the project."
    )
    assumptions: list[str] = Field(
        description="Consolidated list of assumptions made across all evaluations."
    )
