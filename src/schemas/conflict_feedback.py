"""
Conflict Feedback schema.

Used internally by the Parent Supervisor Graph to communicate
constraint violations back to Agent A (Scope Specialist) during
the internal conflict loop.
"""

from pydantic import BaseModel, Field
from src.schemas.cost_estimate import FeatureCost


class ViolatedConstraint(BaseModel):
    """Represents a specific constraint that was not met."""

    constraint_type: str = Field(
        description="Type of constraint. Examples: 'budget', 'timeline', 'technical_risk'."
    )
    target_value: float | str = Field(
        description="The target value requested (e.g., user budget)."
    )
    current_value: float | str = Field(
        description="The actual value estimated (e.g., total estimated cost)."
    )
    overshoot: float | None = Field(
        default=None,
        description="How much the constraint was exceeded by (e.g., budget delta)."
    )


class ConflictFeedback(BaseModel):
    """
    Data passed back to Agent A when constraints fail.
    Instructs the agent on what to trim or change.
    """

    violated_constraints: list[ViolatedConstraint] = Field(
        description="List of constraints that failed."
    )
    highest_cost_features: list[FeatureCost] = Field(
        default_factory=list,
        description="The most expensive features, guiding what to trim."
    )
    iteration_number: int = Field(
        description="Which loop iteration we are on (1, 2, or 3)."
    )
    previous_trims: list[str] = Field(
        default_factory=list,
        description="Features that were already trimmed in previous iterations."
    )
    guidance: str = Field(
        description=(
            "Specific instruction for the LLM. "
            "Example: 'You are $15,000 over budget. Remove the most expensive "
            "nice-to-have features and do not re-add previously trimmed ones.'"
        )
    )
    optimization_target: str = Field(
        default="scope",
        description="Which department to refine: 'scope', 'architecture', or 'both'."
    )
