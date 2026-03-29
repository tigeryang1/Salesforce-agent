from fastapi.testclient import TestClient

from neo4j_setup.api import create_app


class FakeRepository:
    def health(self):
        return {"status": "ok"}

    def close(self):
        return None

    def get_accounts(self):
        return [{"id": "acct_1", "name": "Acme"}]

    def get_account(self, account_id: str):
        if account_id == "acct_1":
            return {"id": "acct_1", "name": "Acme", "contacts": [], "opportunities": [], "cases": []}
        return None

    def get_account_contacts(self, account_id: str):
        return [{"id": "cont_1", "name": "Amy"}]

    def get_account_opportunities(self, account_id: str):
        return [{"id": "opp_1", "name": "Expansion"}]

    def get_account_cases(self, account_id: str):
        return [{"id": "case_1", "subject": "Billing discrepancy"}]

    def get_opportunities(self):
        return [{"id": "opp_1", "name": "Expansion"}]

    def get_cases(self):
        return [{"id": "case_1", "subject": "Billing discrepancy"}]

    def get_campaigns(self):
        return [{"id": "camp_1", "name": "Spring Promo"}]


def build_client() -> TestClient:
    app = create_app()
    app.router.on_startup.clear()
    app.router.on_shutdown.clear()
    app.state.repo = FakeRepository()
    return TestClient(app)


def test_healthz() -> None:
    client = build_client()
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_account() -> None:
    client = build_client()
    response = client.get("/accounts/acct_1")
    assert response.status_code == 200
    assert response.json()["account"]["id"] == "acct_1"


def test_get_account_not_found() -> None:
    client = build_client()
    response = client.get("/accounts/missing")
    assert response.status_code == 404

