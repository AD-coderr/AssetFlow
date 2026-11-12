import os
import tempfile

# Point the app at a throwaway database before it is imported.
_tmpdir = tempfile.mkdtemp()
os.environ["ASSETFLOW_DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

ASSET = {"asset_tag": "LAP-001", "asset_type": "Laptop", "brand": "Dell", "model": "XPS 13"}


def test_root():
    assert client.get("/").json() == {"message": "AssetFlow API Running"}


def test_asset_crud_and_conflict():
    r = client.post("/assets", json=ASSET)
    assert r.status_code == 201
    asset = r.json()["asset"]
    assert asset["status"] == "AVAILABLE"
    asset_id = asset["id"]

    assert client.post("/assets", json=ASSET).status_code == 409

    assert client.get(f"/assets/{asset_id}").json()["asset_tag"] == "LAP-001"
    assert len(client.get("/assets").json()) == 1

    r = client.put(f"/assets/{asset_id}", json={**ASSET, "status": "IN_REPAIR", "location": "HQ"})
    assert r.status_code == 200
    assert r.json()["asset"]["location"] == "HQ"

    assert client.delete(f"/assets/{asset_id}").status_code == 200
    assert client.get(f"/assets/{asset_id}").status_code == 404
    assert client.delete(f"/assets/{asset_id}").status_code == 404


def test_employee_crud_and_conflict():
    emp = {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"}
    r = client.post("/employees", json=emp)
    assert r.status_code == 201
    emp_id = r.json()["employee"]["id"]

    assert client.post("/employees", json=emp).status_code == 409

    r = client.put(f"/employees/{emp_id}", json={**emp, "department": "IT"})
    assert r.json()["employee"]["department"] == "IT"

    assert client.delete(f"/employees/{emp_id}").status_code == 200
    assert client.get(f"/employees/{emp_id}").status_code == 404


def test_users_never_expose_password_hash():
    for user in client.get("/users").json():
        assert "password_hash" not in user


def test_web_ui_is_served():
    r = client.get("/ui/")
    assert r.status_code == 200
    assert "<title>AssetFlow</title>" in r.text
    assert client.get("/ui/app.js").status_code == 200


def _make_asset(tag, **extra):
    r = client.post("/assets", json={**ASSET, "asset_tag": tag, **extra})
    assert r.status_code == 201, r.text
    return r.json()["asset"]


def _make_employee(email):
    r = client.post("/employees", json={"first_name": "Grace", "last_name": "Hopper", "email": email})
    assert r.status_code == 201, r.text
    return r.json()["employee"]


def test_assign_and_return_flow():
    asset = _make_asset("ASG-001")
    emp = _make_employee("grace1@example.com")
    aid, eid = asset["id"], emp["id"]

    # assign
    r = client.post(f"/assets/{aid}/assign", json={"employee_id": eid, "notes": "New hire"})
    assert r.status_code == 201, r.text
    assignment = r.json()["assignment"]
    assert assignment["is_active"] is True
    assert assignment["returned_at"] is None
    assert assignment["employee"]["id"] == eid

    # asset and employee reflect it
    a = client.get(f"/assets/{aid}").json()
    assert a["status"] == "ASSIGNED"
    assert a["assigned_to"]["id"] == eid
    e = client.get(f"/employees/{eid}").json()
    assert [x["asset_tag"] for x in e["assets"]] == ["ASG-001"]
    assert len(client.get("/assignments", params={"active": True}).json()) >= 1

    # can't double-assign, change status, or delete either side while assigned
    assert client.post(f"/assets/{aid}/assign", json={"employee_id": eid}).status_code == 409
    assert client.put(f"/assets/{aid}", json={**ASSET, "asset_tag": "ASG-001", "status": "RETIRED"}).status_code == 409
    assert client.delete(f"/assets/{aid}").status_code == 409
    assert client.delete(f"/employees/{eid}").status_code == 409

    # other fields can still be edited while assigned
    r = client.put(f"/assets/{aid}", json={**ASSET, "asset_tag": "ASG-001", "status": "ASSIGNED", "location": "Desk 4"})
    assert r.status_code == 200
    assert r.json()["asset"]["assigned_to"]["id"] == eid

    # return
    r = client.post(f"/assets/{aid}/return")
    assert r.status_code == 200
    assert r.json()["assignment"]["is_active"] is False
    assert r.json()["assignment"]["returned_at"] is not None
    a = client.get(f"/assets/{aid}").json()
    assert a["status"] == "AVAILABLE" and a["assigned_to"] is None
    assert client.get(f"/employees/{eid}").json()["assets"] == []
    assert client.post(f"/assets/{aid}/return").status_code == 409

    # history is kept on both sides, newest first
    client.post(f"/assets/{aid}/assign", json={"employee_id": eid})
    history = client.get(f"/assets/{aid}/assignments").json()
    assert [h["is_active"] for h in history] == [True, False]
    assert len(client.get(f"/employees/{eid}/assignments").json()) == 2

    # cleanup works once returned
    client.post(f"/assets/{aid}/return")
    assert client.delete(f"/assets/{aid}").status_code == 200
    assert client.delete(f"/employees/{eid}").status_code == 200


def test_assignment_rules():
    emp = _make_employee("grace2@example.com")

    # only available assets can be assigned
    broken = _make_asset("ASG-002", status="IN_REPAIR")
    r = client.post(f"/assets/{broken['id']}/assign", json={"employee_id": emp["id"]})
    assert r.status_code == 409

    # "ASSIGNED" can't be set by hand
    assert client.post("/assets", json={**ASSET, "asset_tag": "ASG-003", "status": "ASSIGNED"}).status_code == 409
    free = _make_asset("ASG-004")
    r = client.put(f"/assets/{free['id']}", json={**ASSET, "asset_tag": "ASG-004", "status": "ASSIGNED"})
    assert r.status_code == 409

    # unknown asset / employee
    assert client.post("/assets/999999/assign", json={"employee_id": emp["id"]}).status_code == 404
    assert client.post(f"/assets/{free['id']}/assign", json={"employee_id": 999999}).status_code == 404
    assert client.get("/assets/999999/assignments").status_code == 404
