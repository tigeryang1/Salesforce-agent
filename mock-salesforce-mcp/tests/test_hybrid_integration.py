from __future__ import annotations

import os
import socket
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.datastore import DataStore


MONOREPO_ROOT = Path(__file__).resolve().parents[2]
HYBRID_ROOT = MONOREPO_ROOT / "salesforce-hybrid-sim"
if str(HYBRID_ROOT) not in sys.path:
    sys.path.insert(0, str(HYBRID_ROOT))

from salesforce_hybrid_sim.api import create_app  # noqa: E402
from salesforce_hybrid_sim.seed_data import SEED_DATA  # noqa: E402
from salesforce_hybrid_sim.sqlite_store import SQLiteStore  # noqa: E402


def db_path_for_test() -> Path:
    base = HYBRID_ROOT / "data" / "test_runs"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{uuid4().hex}.db"


def local_neo4j_available() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 7687), timeout=1):
            return True
    except OSError:
        return False


def test_datastore_reads_seeded_hybrid_api(monkeypatch) -> None:
    db_path = db_path_for_test()
    SQLiteStore(db_path).seed(SEED_DATA)

    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    client = TestClient(create_app())
    monkeypatch.setenv("MOCK_SF_PREFER_NEO4J", "true")
    monkeypatch.setattr(DataStore, "_request_json", lambda self, path: client.get(path).json())

    store = DataStore()

    assert store.accounts["acct_us_001"].name == "Acme Retail"
    assert store.campaigns["camp_001"].account_id == "acct_us_001"
    assert store.opportunities["opp_001"].stage == "Proposal"
    assert store.cases["case_001"].subject == "Billing discrepancy"


@pytest.mark.skipif(not local_neo4j_available(), reason="Local Neo4j is not reachable on 127.0.0.1:7687")
def test_hybrid_api_can_sync_sqlite_projection_to_local_neo4j(monkeypatch) -> None:
    db_path = db_path_for_test()
    SQLiteStore(db_path).seed(SEED_DATA)

    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    client = TestClient(create_app())

    response = client.post("/admin/sync-graph")

    assert response.status_code == 200
    assert response.json()["synced"] is True
    assert response.json()["counts"]["accounts"] >= 1
