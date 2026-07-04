from typing import TypedDict
from pydantic import BaseModel
from src.schemas.blueprint import ProjectBlueprint
from src.schemas.validated_input import ValidatedInput
from src.schemas.risk_assessment import Risk, RiskAssessment

class RiskList(BaseModel):
    risks: list[Risk]

class RiskState(TypedDict):
    project_blueprint: ProjectBlueprint
    validated_input: ValidatedInput | None
    timeline_risks: list[Risk] | None
    technical_risks: list[Risk] | None
    security_risks: list[Risk] | None
    risk_assessment: RiskAssessment | None
