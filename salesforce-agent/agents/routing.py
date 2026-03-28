from __future__ import annotations

from agents.context import WorkflowState


def route_intent(state: WorkflowState) -> str:
    if state.get("phase") == "done":
        return "end"
    if state.get("phase") in {"finalize", "analyzed"}:
        return "end"

    intent = state.get("intent")
    if intent == "read":
        return "read"
    if intent == "write":
        return "write"
    return "end"


def route_after_analysis(state: WorkflowState) -> str:
    if state.get("error"):
        return "end"
    return "write" if state.get("intent") == "write" else "read"


def route_compliance(state: WorkflowState) -> str:
    if state.get("error"):
        return "blocked"
    if state.get("compliance_cleared"):
        return "approved"
    return "needs_human"

