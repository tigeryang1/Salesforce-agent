from __future__ import annotations


class PromptsService:
    @staticmethod
    def campaign_optimization_review(account_id: str) -> dict:
        return {
            "description": "Guided read-only campaign analysis before any budget changes.",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": (
                            f"Review account '{account_id}' campaign performance and suggest "
                            "optimizations. Do not execute write tools."
                        ),
                    },
                }
            ],
        }

    @staticmethod
    def support_case_triage(case_id: str) -> dict:
        return {
            "description": "Structured triage for an advertiser support case.",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": (
                            f"Triage case '{case_id}'. Summarize issue, severity, owner, "
                            "and next best action."
                        ),
                    },
                }
            ],
        }

    @staticmethod
    def advertiser_health_summary(account_id: str) -> dict:
        return {
            "description": "Account-level health review with risk context.",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": (
                            f"Create health summary for account '{account_id}' with campaign, "
                            "opportunity, and support signals."
                        ),
                    },
                }
            ],
        }

