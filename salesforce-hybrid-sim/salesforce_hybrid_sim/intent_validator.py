from __future__ import annotations

from dataclasses import dataclass
from typing import Any


OBJECT_LABELS = {
    "Account": "Account",
    "Campaign__c": "Campaign",
    "Opportunity": "Opportunity",
    "Case": "Case",
    "Contact": "Contact",
}


@dataclass
class GraphIntentValidator:
    uri: str
    username: str
    password: str
    database: str

    def _driver(self):
        from neo4j import GraphDatabase

        return GraphDatabase.driver(self.uri, auth=(self.username, self.password))

    def validate(
        self,
        account_id: str,
        account_name: str,
        query: str,
        primary_object: str,
        related_objects: list[str],
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        query_text = """
        MATCH (a:Account {id: $account_id})
        OPTIONAL MATCH (a)<-[:WORKS_FOR]-(contact:Contact)
        OPTIONAL MATCH (a)<-[:FOR_ACCOUNT]-(opp:Opportunity)
        OPTIONAL MATCH (a)<-[:FOR_ACCOUNT]-(support_case:Case)
        OPTIONAL MATCH (campaign:Campaign)-[:TARGETS]->(a)
        RETURN a.id AS account_id,
               a.name AS account_name,
               count(DISTINCT contact) AS contact_count,
               count(DISTINCT opp) AS opportunity_count,
               count(DISTINCT support_case) AS case_count,
               count(DISTINCT campaign) AS campaign_count
        """.strip()

        with self._driver() as driver, driver.session(database=self.database) as session:
            record = session.run(query_text, account_id=account_id).single()

        if not record:
            return {
                "available": True,
                "validated": False,
                "anchor_found": False,
                "query": query,
                "account_id": account_id,
                "account_name": account_name,
                "primary_object": primary_object,
                "evidence": [f"Account '{account_id}' was not found in Neo4j."],
                "object_counts": {},
                "supported_objects": [],
                "suggested_primary_object": "Account",
                "needs_clarification": True,
            }

        counts = {
            "Account": 1,
            "Contact": int(record["contact_count"]),
            "Opportunity": int(record["opportunity_count"]),
            "Case": int(record["case_count"]),
            "Campaign__c": int(record["campaign_count"]),
        }

        supported_objects = [name for name, count in counts.items() if count > 0]
        primary_supported = counts.get(primary_object, 0) > 0
        ranked_supported = sorted(
            [
                candidate
                for candidate in candidates
                if counts.get(candidate["object"], 0) > 0
            ],
            key=lambda item: (counts.get(item["object"], 0), item.get("score", 0)),
            reverse=True,
        )
        suggested_primary_object = ranked_supported[0]["object"] if ranked_supported else "Account"

        evidence = [f"Account '{record['account_name']}' exists in Neo4j."]
        for object_name in ["Contact", "Opportunity", "Case", "Campaign__c"]:
            count = counts[object_name]
            if count:
                evidence.append(f"{count} {object_name} record(s) are linked to the account.")

        related_supported = [name for name in related_objects if counts.get(name, 0) > 0]
        needs_clarification = not primary_supported or (
            primary_object == "Account" and len(related_supported) >= 2
        )

        return {
            "available": True,
            "validated": primary_supported,
            "anchor_found": True,
            "query": query,
            "account_id": account_id,
            "account_name": record["account_name"],
            "primary_object": primary_object,
            "object_counts": counts,
            "supported_objects": supported_objects,
            "suggested_primary_object": suggested_primary_object,
            "related_objects": related_supported,
            "needs_clarification": needs_clarification,
            "evidence": evidence,
        }
