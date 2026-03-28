from __future__ import annotations

import re

from app.utility.auth import get_session
from app.datastore import DataStore
from app.utility.errors import MCPError, entity_disambiguation_required
from app.policy import enforce_account_scope, enforce_region, enforce_tool_scope


class DiscoveryService:
    def __init__(self, store: DataStore) -> None:
        self.store = store

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    @staticmethod
    def _keyword_score(query: str, keywords: set[str], *, default: float = 0.0) -> float:
        score = default
        for keyword in keywords:
            if keyword in query:
                score += 0.22 if " " in keyword else 0.18
        return score

    def _account_matches(self, query: str) -> list:
        needle = self._normalize(query)
        exact_matches = []
        fallback_matches = []
        for account in self.store.accounts.values():
            canonical = self._normalize(account.name)
            if canonical in needle:
                exact_matches.append(account)
                continue

            variant = canonical.replace(" us", "").replace(" eu", "")
            if variant and variant in needle:
                fallback_matches.append(account)
        return exact_matches or fallback_matches

    def resolve_company_context(self, token: str, query: str) -> dict:
        session = get_session(self.store, token)
        enforce_tool_scope(session, "resolve_company_context")

        matches = self._account_matches(query)
        if not matches:
            raise MCPError(
                code="VALIDATION_SCHEMA_MISMATCH",
                message=f"No company context matched '{query}'.",
                category="validation",
                layer="intent",
            )
        if len(matches) > 1:
            candidates = [
                {
                    "id": match.id,
                    "label": match.name,
                    "type": "Account",
                    "confidence": 0.72 if session.region == match.region else 0.66,
                }
                for match in matches
            ]
            raise entity_disambiguation_required(query, candidates)

        account = matches[0]
        enforce_account_scope(session, account.id)
        enforce_region(session, account.region)

        normalized = self._normalize(query)
        broad_keywords = {"about", "overview", "summary", "tell me", "show me"}
        object_candidates = [
            {
                "object": "Account",
                "score": min(
                    0.98,
                    0.62
                    + self._keyword_score(
                        normalized,
                        {"account", "company", "advertiser", "customer", "overview", "summary"},
                    ),
                ),
                "reason": "Company-level query is anchored to the account record.",
            },
            {
                "object": "Campaign__c",
                "score": min(
                    0.98,
                    0.28
                    + self._keyword_score(
                        normalized,
                        {"campaign", "marketing", "budget", "spend", "optimize", "ad"},
                    ),
                ),
                "reason": "Campaign intent keywords map to campaign data linked by account_id.",
            },
            {
                "object": "Opportunity",
                "score": min(
                    0.98,
                    0.26
                    + self._keyword_score(
                        normalized,
                        {"deal", "deals", "opportunity", "pipeline", "revenue", "stage", "close"},
                    ),
                ),
                "reason": "Revenue and deal language maps to opportunities linked by account_id.",
            },
            {
                "object": "Case",
                "score": min(
                    0.98,
                    0.24
                    + self._keyword_score(
                        normalized,
                        {"case", "cases", "issue", "issues", "support", "ticket", "problem"},
                    ),
                ),
                "reason": "Support language maps to cases linked by account_id.",
            },
        ]
        object_candidates = sorted(object_candidates, key=lambda item: item["score"], reverse=True)

        top = object_candidates[0]
        second = object_candidates[1]
        is_broad = any(keyword in normalized for keyword in broad_keywords)
        related_objects: list[str] = []
        for candidate in object_candidates[1:]:
            if candidate["score"] >= 0.55 or (is_broad and candidate["score"] >= 0.40):
                related_objects.append(candidate["object"])

        needs_clarification = top["score"] < 0.75 or (top["score"] - second["score"] < 0.10)
        validation_failures: list[str] = []
        if top["object"] != "Account" and top["score"] < 0.75:
            validation_failures.append("No dominant business object was detected from the query.")

        return {
            "query": query,
            "entity_id": account.id,
            "entity_name": account.name,
            "anchor_object": "Account",
            "primary_object": top["object"],
            "primary_confidence": round(top["score"], 2),
            "related_objects": related_objects,
            "candidates": [
                {
                    "object": candidate["object"],
                    "score": round(candidate["score"], 2),
                    "reason": candidate["reason"],
                }
                for candidate in object_candidates
            ],
            "validation": {
                "ok": not validation_failures,
                "failures": validation_failures,
                "relationship_paths": [
                    "Campaign__c.account_id -> Account.id",
                    "Opportunity.account_id -> Account.id",
                    "Case.account_id -> Account.id",
                ],
            },
            "needs_clarification": needs_clarification,
            "clarification_question": (
                "Do you want the company record, campaigns, opportunities, or support cases?"
                if needs_clarification
                else None
            ),
        }

    def search_advertiser(self, token: str, query: str) -> dict:
        session = get_session(self.store, token)
        enforce_tool_scope(session, "search_advertiser")

        matches = [a for a in self.store.accounts.values() if query.lower() in a.name.lower()]
        if not matches:
            raise MCPError(
                code="VALIDATION_SCHEMA_MISMATCH",
                message=f"No advertisers matched '{query}'.",
                category="validation",
                layer="intent",
            )
        if len(matches) > 1:
            candidates = [
                {
                    "id": match.id,
                    "label": match.name,
                    "confidence": 0.72 if "US" in match.name else 0.69,
                }
                for match in matches
            ]
            raise entity_disambiguation_required(query, candidates)

        match = matches[0]
        enforce_account_scope(session, match.id)
        enforce_region(session, match.region)
        return {"id": match.id, "name": match.name, "confidence": 0.94}

    def search_global(self, token: str, query: str, limit: int = 10) -> dict:
        session = get_session(self.store, token)
        enforce_tool_scope(session, "search_global")

        needle = query.lower()
        results: list[dict] = []

        for account in self.store.accounts.values():
            if needle in account.name.lower():
                results.append(
                    {
                        "type": "Account",
                        "id": account.id,
                        "label": account.name,
                        "confidence": 0.86,
                    }
                )

        for campaign in self.store.campaigns.values():
            if needle in campaign.name.lower():
                results.append(
                    {
                        "type": "Campaign__c",
                        "id": campaign.id,
                        "label": campaign.name,
                        "account_id": campaign.account_id,
                        "confidence": 0.78,
                    }
                )

        for case in self.store.cases.values():
            if needle in case.subject.lower():
                results.append(
                    {
                        "type": "Case",
                        "id": case.id,
                        "label": case.subject,
                        "account_id": case.account_id,
                        "confidence": 0.73,
                    }
                )

        for opportunity in self.store.opportunities.values():
            if needle in opportunity.stage.lower():
                results.append(
                    {
                        "type": "Opportunity",
                        "id": opportunity.id,
                        "label": opportunity.stage,
                        "account_id": opportunity.account_id,
                        "confidence": 0.7,
                    }
                )

        if not results:
            raise MCPError(
                code="VALIDATION_SCHEMA_MISMATCH",
                message=f"No global entities matched '{query}'.",
                category="validation",
                layer="intent",
            )

        ranked = sorted(results, key=lambda item: item["confidence"], reverse=True)[: max(1, limit)]
        return {"query": query, "count": len(ranked), "results": ranked}
