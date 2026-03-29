import os

from app.datastore import DataStore


def test_datastore_uses_fixture_data_by_default(monkeypatch) -> None:
    monkeypatch.delenv("MOCK_SF_PREFER_NEO4J", raising=False)
    store = DataStore()
    assert "acct_us_001" in store.accounts


def test_datastore_falls_back_to_fixtures_when_neo4j_fetch_fails(monkeypatch) -> None:
    monkeypatch.setenv("MOCK_SF_PREFER_NEO4J", "true")

    def boom(self):
        raise RuntimeError("graph api unavailable")

    monkeypatch.setattr(DataStore, "_fetch_from_local_api", boom)
    store = DataStore()
    assert "acct_us_001" in store.accounts
    assert "camp_us_001" in store.campaigns


def test_datastore_can_map_local_api_payloads(monkeypatch) -> None:
    monkeypatch.setenv("MOCK_SF_PREFER_NEO4J", "true")

    payloads = {
        "/accounts": {
            "accounts": [
                {"id": "acct_us_001", "name": "Acme Retail", "region": "US", "tier": "Enterprise"}
            ]
        },
        "/campaigns": {
            "campaigns": [
                {
                    "id": "camp_001",
                    "name": "Spring Promo US",
                    "status": "Active",
                    "budget": 120000,
                    "account": {"id": "acct_us_001", "name": "Acme Retail"},
                }
            ]
        },
        "/opportunities": {
            "opportunities": [
                {
                    "id": "opp_001",
                    "name": "Acme Expansion FY26",
                    "stage": "Proposal",
                    "close_date": "2026-05-15",
                    "account": {"id": "acct_us_001", "name": "Acme Retail"},
                }
            ]
        },
        "/cases": {
            "cases": [
                {
                    "id": "case_001",
                    "subject": "Billing discrepancy",
                    "priority": "High",
                    "status": "Open",
                    "account": {"id": "acct_us_001", "name": "Acme Retail"},
                }
            ]
        },
    }

    monkeypatch.setattr(DataStore, "_request_json", lambda self, path: payloads[path])
    store = DataStore()
    assert "acct_us_001" in store.accounts
    assert store.campaigns["camp_001"].account_id == "acct_us_001"
    assert store.opportunities["opp_001"].stage == "Proposal"
