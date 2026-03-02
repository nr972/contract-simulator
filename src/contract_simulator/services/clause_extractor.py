import json
import logging

import anthropic
from fastapi import HTTPException, status

from contract_simulator.core.config import Settings
from contract_simulator.models.contract import ParsedContract
from contract_simulator.prompts.clause_extraction import (
    CLAUSE_EXTRACTION_SYSTEM,
    CLAUSE_EXTRACTION_USER,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 1


async def extract_clauses(raw_text: str, settings: Settings) -> ParsedContract:
    """Use Claude to extract structured clauses from raw contract text."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    prompt = CLAUSE_EXTRACTION_USER.format(contract_text=raw_text)

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            message = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=8192,
                system=CLAUSE_EXTRACTION_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text

            # Strip markdown code fences if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                # Remove first line (```json) and last line (```)
                lines = [l for l in lines[1:] if l.strip() != "```"]
                response_text = "\n".join(lines)

            data = json.loads(response_text)
            return ParsedContract(raw_text=raw_text, **data)

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(
                "Clause extraction JSON parse failed (attempt %d/%d): %s",
                attempt + 1,
                MAX_RETRIES + 1,
                e,
            )
            continue
        except anthropic.APIError as e:
            logger.error("Anthropic API error during clause extraction: %s", e)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to communicate with the AI service. Please try again.",
            ) from e

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Failed to parse contract structure. Please try again.",
    ) from last_error
