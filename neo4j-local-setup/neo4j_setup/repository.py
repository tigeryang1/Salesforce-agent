from __future__ import annotations

from typing import Any


class SalesforceGraphRepository:
    def __init__(self, driver, database: str) -> None:
        self.driver = driver
        self.database = database

    def close(self) -> None:
        self.driver.close()

    def _run(self, query: str, **params: Any) -> list[dict[str, Any]]:
        with self.driver.session(database=self.database) as session:
            return [record.data() for record in session.run(query, **params)]

    def health(self) -> dict[str, Any]:
        rows = self._run("RETURN 'ok' AS status")
        return rows[0] if rows else {"status": "unknown"}

    def get_accounts(self) -> list[dict[str, Any]]:
        query = """
        MATCH (a:Account)
        RETURN a {
            .id, .name, .industry, .region, .tier, .status
        } AS account
        ORDER BY account.name
        """
        return [row["account"] for row in self._run(query)]

    def get_account(self, account_id: str) -> dict[str, Any] | None:
        query = """
        MATCH (a:Account {id: $account_id})
        OPTIONAL MATCH (a)<-[:WORKS_FOR]-(c:Contact)
        OPTIONAL MATCH (a)<-[:FOR_ACCOUNT]-(o:Opportunity)
        OPTIONAL MATCH (a)<-[:FOR_ACCOUNT]-(k:Case)
        RETURN a {
            .id, .name, .industry, .region, .tier, .status,
            contacts: collect(DISTINCT c {.id, .name, .email, .title}),
            opportunities: collect(DISTINCT o {.id, .name, .stage, .amount, .status}),
            cases: collect(DISTINCT k {.id, .subject, .priority, .status})
        } AS account
        """
        rows = self._run(query, account_id=account_id)
        if not rows:
            return None
        payload = rows[0]["account"]
        payload["contacts"] = [item for item in payload["contacts"] if item.get("id")]
        payload["opportunities"] = [item for item in payload["opportunities"] if item.get("id")]
        payload["cases"] = [item for item in payload["cases"] if item.get("id")]
        return payload

    def get_account_contacts(self, account_id: str) -> list[dict[str, Any]]:
        query = """
        MATCH (c:Contact)-[:WORKS_FOR]->(:Account {id: $account_id})
        RETURN c {.id, .name, .email, .title} AS contact
        ORDER BY contact.name
        """
        return [row["contact"] for row in self._run(query, account_id=account_id)]

    def get_account_opportunities(self, account_id: str) -> list[dict[str, Any]]:
        query = """
        MATCH (o:Opportunity)-[:FOR_ACCOUNT]->(:Account {id: $account_id})
        OPTIONAL MATCH (u:User)-[:OWNS]->(o)
        RETURN o {
            .id, .name, .stage, .amount, .close_date, .status,
            owner: head(collect(DISTINCT u {.id, .name, .role}))
        } AS opportunity
        ORDER BY opportunity.name
        """
        return [row["opportunity"] for row in self._run(query, account_id=account_id)]

    def get_account_cases(self, account_id: str) -> list[dict[str, Any]]:
        query = """
        MATCH (k:Case)-[:FOR_ACCOUNT]->(:Account {id: $account_id})
        OPTIONAL MATCH (u:User)-[:OWNS]->(k)
        RETURN k {
            .id, .subject, .priority, .status, .opened_at,
            owner: head(collect(DISTINCT u {.id, .name, .role}))
        } AS case_item
        ORDER BY case_item.opened_at DESC
        """
        return [row["case_item"] for row in self._run(query, account_id=account_id)]

    def get_opportunities(self) -> list[dict[str, Any]]:
        query = """
        MATCH (o:Opportunity)-[:FOR_ACCOUNT]->(a:Account)
        OPTIONAL MATCH (u:User)-[:OWNS]->(o)
        RETURN o {
            .id, .name, .stage, .amount, .close_date, .status,
            account: a {.id, .name},
            owner: head(collect(DISTINCT u {.id, .name, .role}))
        } AS opportunity
        ORDER BY opportunity.name
        """
        return [row["opportunity"] for row in self._run(query)]

    def get_cases(self) -> list[dict[str, Any]]:
        query = """
        MATCH (k:Case)-[:FOR_ACCOUNT]->(a:Account)
        OPTIONAL MATCH (u:User)-[:OWNS]->(k)
        RETURN k {
            .id, .subject, .priority, .status, .opened_at,
            account: a {.id, .name},
            owner: head(collect(DISTINCT u {.id, .name, .role}))
        } AS case_item
        ORDER BY case_item.opened_at DESC
        """
        return [row["case_item"] for row in self._run(query)]

    def get_campaigns(self) -> list[dict[str, Any]]:
        query = """
        MATCH (c:Campaign)-[:TARGETS]->(a:Account)
        OPTIONAL MATCH (c)-[:INFLUENCED]->(o:Opportunity)
        RETURN c {
            .id, .name, .status, .budget, .channel,
            account: a {.id, .name},
            influenced_opportunities: collect(DISTINCT o {.id, .name, .stage})
        } AS campaign
        ORDER BY campaign.name
        """
        rows = [row["campaign"] for row in self._run(query)]
        for row in rows:
            row["influenced_opportunities"] = [
                item for item in row["influenced_opportunities"] if item.get("id")
            ]
        return rows

