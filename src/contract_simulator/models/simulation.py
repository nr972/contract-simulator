from typing import Literal

from pydantic import BaseModel

from contract_simulator.models.contract import ParsedContract


class SimulationRequest(BaseModel):
    parsed_contract: ParsedContract
    scenario_id: str
    parameters: dict[str, str | int | float | bool] = {}


class ClauseAnalysis(BaseModel):
    clause_id: str
    clause_title: str
    is_triggered: bool
    triggered_obligations: list[str]
    timelines: list[str]
    liability_exposure: str | None = None
    ambiguities: list[str]
    risk_level: Literal["low", "medium", "high"]
    reasoning: str


class SimulationSummary(BaseModel):
    total_clauses_analyzed: int
    triggered_clauses: int
    key_obligations: list[str]
    critical_timelines: list[str]
    total_liability_exposure: str
    high_risk_areas: list[str]
    overall_risk_assessment: str


class SimulationEvent(BaseModel):
    event_type: Literal["clause_analysis", "summary", "error", "text_delta"]
    data: ClauseAnalysis | SimulationSummary | str
