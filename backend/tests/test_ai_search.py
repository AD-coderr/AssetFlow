import json
import os
import tempfile

# Same throwaway-database setup as test_api.py; whichever file is imported
# first decides the location, and both then share the one app instance.
os.environ.setdefault("ASSETFLOW_DATABASE_URL", f"sqlite:///{tempfile.mkdtemp()}/test.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.ai import llm  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture
def ai_on(monkeypatch):
    monkeypatch.setenv("ASSETFLOW_LLM_BASE_URL", "http://llm.test/v1")
    monkeypatch.setenv("ASSETFLOW_LLM_MODEL", "test-model")


@pytest.fixture
def answer(monkeypatch):
    """Replace the real LLM call; returns the prompts it was called with."""
    calls = []

    def set_reply(reply):
        def fake_complete(system, user):
            calls.append({"system": system, "user": user})
            if isinstance(reply, Exception):
                raise reply
            return reply if isinstance(reply, str) else json.dumps(reply)

        monkeypatch.setattr(llm, "complete", fake_complete)
        return calls

    return set_reply


@pytest.fixture
def inventory():
    """Three assets and one employee holding one of them; removed afterwards."""

    def post(path, body):
        r = client.post(path, json=body)
        assert r.status_code == 201, r.text
        return r.json()

    base = {"brand": "Dell", "model": "XPS 13"}
    assets = [
        post("/assets", {**base, "asset_tag": "AI-LAP-1", "asset_type": "Laptop", "location": "Berlin"})["asset"],
        post("/assets", {**base, "asset_tag": "AI-LAP-2", "asset_type": "Laptop", "location": "Hamburg"})["asset"],
        post(
            "/assets",
            {"asset_tag": "AI-MON-1", "asset_type": "Monitor", "brand": "LG", "model": "27UL", "location": "Berlin", "status": "IN_REPAIR"},
        )["asset"],
    ]
    employee = post(
        "/employees",
        {"first_name": "Ada", "last_name": "Lovelace", "email": "ada.ai@example.com", "department": "Engineering"},
    )["employee"]
    post(f"/assets/{assets[1]['id']}/assign", {"employee_id": employee["id"]})

    yield {"assets": assets, "employee": employee}

    client.post(f"/assets/{assets[1]['id']}/return")
    for asset in assets:
        assert client.delete(f"/assets/{asset['id']}").status_code == 200
    assert client.delete(f"/employees/{employee['id']}").status_code == 200


def ask(question="which ones?"):
    return client.post("/ai/search", json={"question": question})


def tags(response):
    """Matching tags from this file's inventory (ignores other tests' leftovers)."""
    return [a["asset_tag"] for a in response.json()["assets"] if a["asset_tag"].startswith("AI-")]


def test_disabled_without_configuration(monkeypatch):
    monkeypatch.delenv("ASSETFLOW_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("ASSETFLOW_LLM_MODEL", raising=False)
    assert client.get("/ai/status").json() == {"enabled": False}
    assert ask().status_code == 503


def test_status_enabled_when_configured(ai_on):
    assert client.get("/ai/status").json() == {"enabled": True}


def test_filters_by_type_location_and_status(ai_on, answer, inventory):
    calls = answer({"asset_type": "laptop", "location": "Berlin", "status": "available"})
    r = ask("Which laptops in Berlin are free?")
    assert r.status_code == 200, r.text
    assert tags(r) == ["AI-LAP-1"]
    body = r.json()
    assert body["filters"]["status"] == "AVAILABLE"
    assert body["summary"] == "1 asset · status: Available · type: laptop · location: Berlin"
    # the question is passed as data, and known values are offered to the model
    assert calls[0]["user"] == "Which laptops in Berlin are free?"
    assert "Laptop" in calls[0]["system"] and "Engineering" in calls[0]["system"]


def test_filters_by_current_holder_and_department(ai_on, answer, inventory):
    answer({"assigned_to": "ada lovelace"})
    assert tags(ask()) == ["AI-LAP-2"]

    answer({"department": "engineering", "status": "ASSIGNED"})
    assert tags(ask()) == ["AI-LAP-2"]

    answer({"assigned_to": "nobody"})
    assert tags(ask()) == []

    # a returned asset no longer counts as held by that employee
    client.post(f"/assets/{inventory['assets'][1]['id']}/return")
    answer({"assigned_to": "ada"})
    assert tags(ask()) == []
    client.post(f"/assets/{inventory['assets'][1]['id']}/assign", json={"employee_id": inventory["employee"]["id"]})


def test_free_text_and_like_wildcards_are_literal(ai_on, answer, inventory):
    answer({"text": "ai-mon"})
    assert tags(ask()) == ["AI-MON-1"]

    answer({"text": "%"})
    assert tags(ask()) == []


def test_reply_wrapped_in_prose_and_unknown_keys(ai_on, answer, inventory):
    answer('Sure! ```json\n{"status": "in repair", "drop_table": "assets"}\n``` Hope that helps.')
    r = ask()
    assert tags(r) == ["AI-MON-1"]
    assert "drop_table" not in r.json()["filters"]


def test_empty_filter_returns_everything_with_a_note(ai_on, answer, inventory):
    answer({})
    r = ask("tell me a joke")
    assert r.status_code == 200
    assert tags(r) == ["AI-LAP-1", "AI-LAP-2", "AI-MON-1"]
    assert len(r.json()["assets"]) == len(client.get("/assets").json())
    assert "Couldn't turn that into a filter" in r.json()["summary"]


@pytest.mark.parametrize(
    "reply",
    ["no json here", "[1, 2]", '{"status": "EXPLODED"}', '{"location": ["Berlin"]}', '{"status": '],
)
def test_unusable_model_answers_give_502(ai_on, answer, reply):
    answer(reply)
    assert ask().status_code == 502


def test_provider_failure_gives_502(ai_on, answer):
    answer(llm.LLMError("The AI provider could not be reached"))
    r = ask()
    assert r.status_code == 502
    assert r.json()["detail"] == "The AI provider could not be reached"


def test_question_is_validated(ai_on, answer):
    answer({})
    assert client.post("/ai/search", json={"question": "   "}).status_code == 422
    assert client.post("/ai/search", json={"question": "x" * 301}).status_code == 422
    assert client.post("/ai/search", json={}).status_code == 422
