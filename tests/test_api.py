def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_list_scenarios(test_client):
    response = test_client.get("/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 6
    ids = {s["id"] for s in scenarios}
    assert "data_breach" in ids


def test_get_scenario_detail(test_client):
    response = test_client.get("/scenarios/data_breach")
    assert response.status_code == 200
    scenario = response.json()
    assert scenario["name"] == "Data Breach"
    assert len(scenario["parameters"]) > 0


def test_get_scenario_not_found(test_client):
    response = test_client.get("/scenarios/nonexistent")
    assert response.status_code == 404


def test_upload_invalid_extension(test_client):
    response = test_client.post(
        "/contracts/parse",
        files={"file": ("test.txt", b"some content", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_empty_file(test_client):
    response = test_client.post(
        "/contracts/parse",
        files={"file": ("test.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_wrong_magic_bytes(test_client):
    response = test_client.post(
        "/contracts/parse",
        files={"file": ("test.pdf", b"not a pdf", "application/pdf")},
    )
    assert response.status_code == 400
    assert "content does not match" in response.json()["detail"]


def test_upload_path_traversal(test_client):
    response = test_client.post(
        "/contracts/parse",
        files={"file": ("../../../etc/passwd", b"%PDF-test", "application/pdf")},
    )
    assert response.status_code == 400


def test_shutdown_endpoint(test_client):
    """Shutdown endpoint returns 200 and schedules SIGTERM (mocked)."""
    from unittest.mock import patch

    with patch("contract_simulator.api.main.threading.Thread") as mock_thread:
        response = test_client.post("/api/v1/shutdown")

    assert response.status_code == 200
    assert response.json() == {"status": "shutting_down"}
    mock_thread.assert_called_once()
    mock_thread.return_value.start.assert_called_once()


def test_suggest_defaults(test_client, sample_parsed_contract):
    """Suggest-defaults endpoint returns merged defaults with Claude response mocked."""
    import json
    from unittest.mock import MagicMock, patch

    mock_suggestions = json.dumps({"records_affected": 50000})
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=mock_suggestions)]

    with patch("contract_simulator.services.parameter_suggester.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_cls.return_value = mock_client

        response = test_client.post(
            "/scenarios/data_breach/suggest-defaults",
            json={"clauses": sample_parsed_contract["clauses"]},
        )

    assert response.status_code == 200
    defaults = response.json()["defaults"]
    # Claude suggestion should override template default
    assert defaults["records_affected"] == 50000
    # Template defaults should still be present for other params
    assert "data_types" in defaults
    assert "breach_source" in defaults


def test_suggest_defaults_not_found(test_client, sample_parsed_contract):
    """Suggest-defaults returns 404 for unknown scenario."""
    response = test_client.post(
        "/scenarios/nonexistent/suggest-defaults",
        json={"clauses": sample_parsed_contract["clauses"]},
    )
    assert response.status_code == 404
