from agents.routing import route_after_analysis, route_compliance, route_intent


def test_route_intent_read() -> None:
    assert route_intent({"intent": "read", "phase": "route"}) == "read"


def test_route_intent_write() -> None:
    assert route_intent({"intent": "write", "phase": "route"}) == "write"


def test_route_intent_done_ends() -> None:
    assert route_intent({"intent": "read", "phase": "done"}) == "end"


def test_route_after_analysis_write() -> None:
    assert route_after_analysis({"intent": "write"}) == "write"


def test_route_after_analysis_error_ends() -> None:
    assert route_after_analysis({"intent": "write", "error": {"code": "X"}}) == "end"


def test_route_compliance_blocked_on_error() -> None:
    assert route_compliance({"error": {"code": "X"}}) == "blocked"


def test_route_compliance_approved() -> None:
    assert route_compliance({"compliance_cleared": True}) == "approved"


def test_route_compliance_needs_human() -> None:
    assert route_compliance({"compliance_cleared": False}) == "needs_human"

