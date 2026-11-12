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

    r = client.put(f"/assets/{asset_id}", json={**ASSET, "status": "ASSIGNED", "location": "HQ"})
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
