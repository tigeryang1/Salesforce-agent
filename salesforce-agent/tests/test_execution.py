import asyncio

from agents.nodes.execution import make_execution_node


class FakeExecutionAgent:
    async def ainvoke(self, payload):
        return {"output": "write executed successfully"}


def test_execution_requires_tool_name() -> None:
    node = make_execution_node(execution_agent=FakeExecutionAgent(), session_token="tok_alice_us")
    result = asyncio.run(node({"proposed_action": {"arguments": {"idempotency_key": "idem_1"}}}))
    assert result["error"]["code"] == "VALIDATION_SCHEMA_MISMATCH"


def test_execution_requires_idempotency_key() -> None:
    node = make_execution_node(execution_agent=FakeExecutionAgent(), session_token="tok_alice_us")
    result = asyncio.run(
        node(
            {
                "proposed_action": {
                    "tool": "create_support_case",
                    "arguments": {"account_id": "acct_us_001"},
                }
            }
        )
    )
    assert result["error"]["message"] == "idempotency_key is required."


def test_execution_requires_approval_for_high_risk() -> None:
    node = make_execution_node(execution_agent=FakeExecutionAgent(), session_token="tok_alice_us")
    result = asyncio.run(
        node(
            {
                "proposed_action": {
                    "tool": "update_campaign_budget",
                    "arguments": {"campaign_id": "camp_us_001", "idempotency_key": "idem_2"},
                }
            }
        )
    )
    assert result["error"]["code"] == "APPROVAL_REQUIRED"


def test_execution_succeeds_for_low_risk_write() -> None:
    node = make_execution_node(execution_agent=FakeExecutionAgent(), session_token="tok_alice_us")
    result = asyncio.run(
        node(
            {
                "proposed_action": {
                    "tool": "create_support_case",
                    "arguments": {
                        "account_id": "acct_us_001",
                        "subject": "Need help",
                        "priority": "High",
                        "idempotency_key": "idem_3",
                    },
                }
            }
        )
    )
    assert result["phase"] == "finalize"
    assert "write executed successfully" in result["recommendations"][0]["execution_result"]

