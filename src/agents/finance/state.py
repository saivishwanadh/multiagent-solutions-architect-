from typing import TypedDict, Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from src.schemas.blueprint import ProjectBlueprint
from src.schemas.cost_estimate import CostEstimate, CostBreakdown, FeatureCost
from src.schemas.validated_input import ValidatedInput

class DevelopmentCostData(BaseModel):
    team_size: int = Field(description="Estimated team size")
    timeline_weeks: int = Field(description="Estimated timeline in weeks")
    development_cost: float = Field(description="Total development cost")
    cost_per_feature: list[FeatureCost] = Field(description="Cost breakdown per feature")

class FinanceState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    project_blueprint: ProjectBlueprint
    validated_input: ValidatedInput | None
    dev_cost_data: DevelopmentCostData | None
    infra_cost_data: CostBreakdown | None
    cost_estimate: CostEstimate | None
