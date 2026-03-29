from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from salesforce_hybrid_sim.api import create_app


def db_path_for_test() -> Path:
    base = Path(__file__).resolve().parents[1] / "data" / "test_runs"
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{uuid4().hex}.db"
    if path.exists():
        path.unlink()
    return path


def test_healthz(monkeypatch) -> None:
    db_path = db_path_for_test()
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    client = TestClient(create_app())
    client.post("/admin/init-db")
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_seed_and_get_accounts(monkeypatch) -> None:
    db_path = db_path_for_test()
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    client = TestClient(create_app())
    client.post("/admin/init-db")
    client.post("/admin/seed")
    response = client.get("/accounts")
    assert response.status_code == 200
    assert len(response.json()["accounts"]) >= 1


def test_related_resources_include_nested_account_refs(monkeypatch) -> None:
    db_path = db_path_for_test()
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    client = TestClient(create_app())
    client.post("/admin/init-db")
    client.post("/admin/seed")

    campaign = client.get("/campaigns").json()["campaigns"][0]
    opportunity = client.get("/opportunities").json()["opportunities"][0]
    case = client.get("/cases").json()["cases"][0]

    assert campaign["account"]["id"] == campaign["account_id"]
    assert opportunity["account"]["id"] == opportunity["account_id"]
    assert case["account"]["id"] == case["account_id"]
