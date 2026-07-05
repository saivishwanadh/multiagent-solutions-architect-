from typing import TypedDict, Annotated
from pydantic import BaseModel
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from src.schemas.blueprint import ProjectBlueprint
from src.schemas.validated_input import ValidatedInput
from src.schemas.risk_assessment import Risk, RiskAssessment

class RiskList(BaseModel):
    risks: list[Risk]

class RiskState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    project_blueprint: ProjectBlueprint
    validated_input: ValidatedInput | None
    parsed_requirements: str | None
    timeline_risks: list[Risk] | None
    technical_risks: list[Risk] | None
    security_risks: list[Risk] | None
    risk_assessment: RiskAssessment | None
