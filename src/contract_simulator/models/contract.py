from pydantic import BaseModel


class Clause(BaseModel):
    id: str
    title: str
    section_number: str
    content: str
    clause_type: str  # e.g., liability, indemnification, termination, notice, etc.


class ParsedContract(BaseModel):
    contract_title: str
    parties: list[str]
    effective_date: str | None = None
    clauses: list[Clause]
    raw_text: str
