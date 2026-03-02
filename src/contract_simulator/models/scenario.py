from pydantic import BaseModel


class ScenarioParameter(BaseModel):
    name: str
    param_type: str  # str, int, float, bool
    description: str
    default_value: str | int | float | bool | None = None
    options: list[str] | None = None  # For enum-like parameters


class Scenario(BaseModel):
    id: str
    name: str
    description: str
    category: str
    parameters: list[ScenarioParameter]
    analysis_guidance: str  # Instructions for Claude on what to focus on
