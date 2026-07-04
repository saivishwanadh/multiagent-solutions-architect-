from pydantic import BaseModel, Field

class ScenarioResult(BaseModel):
    """Result of evaluating one scenario."""
    label: str = Field(description="Scenario label, e.g. 'Scenario A: Cloud APIs'.")
    total_cost: float = Field(description="Total estimated cost for this scenario.")
    timeline_weeks: int = Field(description="Estimated timeline in weeks.")
    risk_level: str = Field(description="Overall risk level: LOW/MEDIUM/HIGH/CRITICAL.")
    pros: list[str] = Field(description="Advantages of this scenario.")
    cons: list[str] = Field(description="Disadvantages of this scenario.")

class ScenarioComparison(BaseModel):
    """Output of Category 4 Trade-off analysis."""
    scenario_a: ScenarioResult = Field(description="First scenario evaluation.")
    scenario_b: ScenarioResult = Field(description="Second scenario evaluation.")
    recommendation: str = Field(description="Which scenario is recommended and why.")
    key_tradeoffs: list[str] = Field(description="The critical differences between scenarios.")
