from fastapi import APIRouter, Depends, UploadFile

from contract_simulator.core.config import Settings, get_settings
from contract_simulator.core.security import validate_upload
from contract_simulator.models.contract import ParsedContract
from contract_simulator.services.clause_extractor import extract_clauses
from contract_simulator.services.parser import extract_text

router = APIRouter()


@router.post("/parse", response_model=ParsedContract)
async def parse_contract(
    file: UploadFile,
    settings: Settings = Depends(get_settings),
) -> ParsedContract:
    """Upload a contract file (PDF or DOCX) and parse it into structured clauses."""
    content = await validate_upload(file, settings)
    raw_text = extract_text(content, file.filename)  # type: ignore[arg-type]
    return await extract_clauses(raw_text, settings)
