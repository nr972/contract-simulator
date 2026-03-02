import json
from unittest.mock import MagicMock, patch

import pytest

from contract_simulator.models.contract import ParsedContract
from contract_simulator.services.clause_extractor import extract_clauses


MOCK_CLAUDE_RESPONSE = json.dumps({
    "contract_title": "Test Agreement",
    "parties": ["Party A", "Party B"],
    "effective_date": "2026-01-01",
    "clauses": [
        {
            "id": "clause_1",
            "title": "Confidentiality",
            "section_number": "1",
            "content": "Each party shall maintain confidentiality.",
            "clause_type": "confidentiality",
        },
        {
            "id": "clause_2",
            "title": "Termination",
            "section_number": "2",
            "content": "Either party may terminate with 30 days notice.",
            "clause_type": "termination",
        },
    ],
})


@pytest.mark.asyncio
async def test_extract_clauses_success(settings):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=MOCK_CLAUDE_RESPONSE)]

    with patch("contract_simulator.services.clause_extractor.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_cls.return_value = mock_client

        result = await extract_clauses("Test contract text", settings)

    assert isinstance(result, ParsedContract)
    assert result.contract_title == "Test Agreement"
    assert len(result.clauses) == 2
    assert result.clauses[0].clause_type == "confidentiality"
    assert result.raw_text == "Test contract text"


@pytest.mark.asyncio
async def test_extract_clauses_strips_markdown_fences(settings):
    fenced_response = f"```json\n{MOCK_CLAUDE_RESPONSE}\n```"
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=fenced_response)]

    with patch("contract_simulator.services.clause_extractor.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_cls.return_value = mock_client

        result = await extract_clauses("Test contract text", settings)

    assert isinstance(result, ParsedContract)
    assert len(result.clauses) == 2


@pytest.mark.asyncio
async def test_extract_clauses_retries_on_bad_json(settings):
    bad_message = MagicMock()
    bad_message.content = [MagicMock(text="not valid json")]

    good_message = MagicMock()
    good_message.content = [MagicMock(text=MOCK_CLAUDE_RESPONSE)]

    with patch("contract_simulator.services.clause_extractor.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [bad_message, good_message]
        mock_cls.return_value = mock_client

        result = await extract_clauses("Test contract text", settings)

    assert isinstance(result, ParsedContract)
    assert mock_client.messages.create.call_count == 2


@pytest.mark.asyncio
async def test_extract_clauses_fails_after_retries(settings):
    bad_message = MagicMock()
    bad_message.content = [MagicMock(text="not valid json")]

    with patch("contract_simulator.services.clause_extractor.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = bad_message
        mock_cls.return_value = mock_client

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await extract_clauses("Test contract text", settings)
        assert exc_info.value.status_code == 502
