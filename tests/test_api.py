def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_list_scenarios(test_client):
    response = test_client.get("/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 5
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
