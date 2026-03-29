from __future__ import annotations

from typing import Any


class Neo4jProjector:
    def __init__(self, uri: str, username: str, password: str, database: str) -> None:
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database

    def _driver(self):
        from neo4j import GraphDatabase

        if not self.password:
            raise ValueError("Missing NEO4J_PASSWORD. Set it before syncing the graph.")
        return GraphDatabase.driver(self.uri, auth=(self.username, self.password))

    @staticmethod
    def _batch(session, query: str, rows: list[dict[str, Any]]) -> None:
        if rows:
            session.run(query, rows=rows).consume()

    def sync_all(self, bundle: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        driver = self._driver()
        try:
            with driver.session(database=self.database) as session:
                session.run("MATCH (n) DETACH DELETE n").consume()
                self._batch(session, "UNWIND $rows AS row MERGE (n:Account {id: row.id}) SET n += row", bundle["accounts"])
                self._batch(session, "UNWIND $rows AS row MERGE (n:User {id: row.id}) SET n += row", bundle["users"])
                self._batch(session, "UNWIND $rows AS row MERGE (n:Contact {id: row.id}) SET n += row WITH n, row MATCH (a:Account {id: row.account_id}) MERGE (n)-[:WORKS_FOR]->(a)", bundle["contacts"])
                self._batch(session, "UNWIND $rows AS row MERGE (n:Opportunity {id: row.id}) SET n += row WITH n, row MATCH (a:Account {id: row.account_id}) MERGE (n)-[:FOR_ACCOUNT]->(a) WITH n, row MATCH (u:User {id: row.owner_user_id}) MERGE (u)-[:OWNS]->(n)", bundle["opportunities"])
                self._batch(session, "UNWIND $rows AS row MERGE (n:Case {id: row.id}) SET n += row WITH n, row MATCH (a:Account {id: row.account_id}) MERGE (n)-[:FOR_ACCOUNT]->(a) WITH n, row MATCH (u:User {id: row.owner_user_id}) MERGE (u)-[:OWNS]->(n)", bundle["cases"])
                self._batch(session, "UNWIND $rows AS row MERGE (n:Campaign {id: row.id}) SET n += row WITH n, row MATCH (a:Account {id: row.account_id}) MERGE (n)-[:TARGETS]->(a)", bundle["campaigns"])
                self._batch(session, "UNWIND $rows AS row MERGE (n:Task {id: row.id}) SET n += row", bundle["tasks"])
                self._batch(session, "UNWIND $rows AS row MATCH (p:Account {id: row.parent_account_id}) MATCH (c:Account {id: row.child_account_id}) MERGE (p)-[:PARENT_OF]->(c)", bundle["account_hierarchy"])
                self._batch(session, "UNWIND $rows AS row MATCH (c:Campaign {id: row.campaign_id}) MATCH (o:Opportunity {id: row.opportunity_id}) MERGE (c)-[:INFLUENCED]->(o)", bundle["campaign_influence"])
                self._batch(session, "UNWIND $rows AS row MATCH (o:Opportunity {id: row.opportunity_id}) MATCH (c:Contact {id: row.contact_id}) MERGE (o)-[:INVOLVES_CONTACT]->(c)", bundle["opportunity_contacts"])
                self._batch(session, "UNWIND $rows AS row MATCH (t:Task {id: row.id}) MATCH (o:Opportunity {id: row.opportunity_id}) MERGE (t)-[:RELATED_TO]->(o)", [r for r in bundle["tasks"] if r.get("opportunity_id")])
                self._batch(session, "UNWIND $rows AS row MATCH (t:Task {id: row.id}) MATCH (c:Case {id: row.case_id}) MERGE (t)-[:RELATED_TO]->(c)", [r for r in bundle["tasks"] if r.get("case_id")])
        finally:
            driver.close()
        return {key: len(value) for key, value in bundle.items()}

