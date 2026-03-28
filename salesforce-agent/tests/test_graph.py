import asyncio

from agents.context import AgentContext
from agents.system import build_agent_system


class FakeTool:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeBlob:
    def __init__(self, text: str) -> None:
        self._text = text

    def as_string(self) -> str:
        return self._text


class FakeClient:
    async def get_tools(self):
        return [
            FakeTool("search_advertiser"),
            FakeTool("search_global"),
            FakeTool("resolve_company_context"),
            FakeTool("create_support_case"),
            FakeTool("update_campaign_budget"),
            FakeTool("optimize_campaign"),
        ]

    async def get_resources(self, uris=None):
        return [
            FakeBlob("account summary"),
            FakeBlob("campaign list"),
            FakeBlob("opportunity list"),
        ]


class FakeAgent:
    def __init__(self, output: str) -> None:
        self.output = output

    async def ainvoke(self, payload):
        return {"output": self.output}


def test_build_agent_system_read_path(monkeypatch) -> None:
    async def fake_build_mcp_client(session_token: str, mcp_url: str):
        return FakeClient()

    outputs = iter(
        [
            FakeAgent("final response from supervisor"),
            FakeAgent(
                '{"entity_id":"acct_us_001","primary_object":"Account","primary_confidence":0.94,'
                '"related_objects":["Campaign__c","Opportunity"],'
                '"candidates":[{"object":"Account","score":0.94}],"validation":{"ok":true,"failures":[]}}'
            ),
            FakeAgent("context summary"),
            FakeAgent("analysis recommendation"),
            FakeAgent("unused execution"),
        ]
    )

    def fake_create_agent(*args, **kwargs):
        return next(outputs)

    monkeypatch.setattr("agents.system.build_mcp_client", fake_build_mcp_client)
    monkeypatch.setattr("agents.system.build_chat_model", lambda model_name: object())
    monkeypatch.setattr("agents.system.create_agent", fake_create_agent)

    context = AgentContext(
        user_id="alice",
        org_id="US",
        region="US",
        approved_tool_set=[
            "search_advertiser",
            "create_support_case",
            "update_campaign_budget",
            "optimize_campaign",
        ],
        account_scope="acct_us_001",
    )

    system = asyncio.run(
        build_agent_system(
            session_token="tok_alice_us",
            mcp_url="http://127.0.0.1:8000/mcp",
            model="openai:gpt-5.3-codex",
            agent_context=context,
        )
    )
    result = asyncio.run(
        system.run("Analyze Nike account and suggest optimizations", thread_id="read-1")
    )
    assert result["phase"] == "done"
    assert result["final_response"] == "final response from supervisor"
    assert result["entity_id"] == "acct_us_001"
    assert result["primary_object"] == "Account"


def test_build_agent_system_write_path_reaches_approval_gate(monkeypatch) -> None:
    async def fake_build_mcp_client(session_token: str, mcp_url: str):
        return FakeClient()

    outputs = iter(
        [
            FakeAgent("final response after execution"),
            FakeAgent(
                '{"entity_id":"acct_us_001","primary_object":"Campaign__c","primary_confidence":0.91,'
                '"related_objects":["Account"],'
                '"candidates":[{"object":"Campaign__c","score":0.91}],"validation":{"ok":true,"failures":[]}}'
            ),
            FakeAgent("context summary"),
            FakeAgent("analysis recommendation"),
            FakeAgent("execution completed"),
        ]
    )

    def fake_create_agent(*args, **kwargs):
        return next(outputs)

    monkeypatch.setattr("agents.system.build_mcp_client", fake_build_mcp_client)
    monkeypatch.setattr("agents.system.build_chat_model", lambda model_name: object())
    monkeypatch.setattr("agents.system.create_agent", fake_create_agent)

    context = AgentContext(
        user_id="alice",
        org_id="US",
        region="US",
        approved_tool_set=[
            "search_advertiser",
            "create_support_case",
            "update_campaign_budget",
            "optimize_campaign",
        ],
        account_scope="acct_us_001",
    )

    system = asyncio.run(
        build_agent_system(
            session_token="tok_alice_us",
            mcp_url="http://127.0.0.1:8000/mcp",
            model="openai:gpt-5.3-codex",
            agent_context=context,
        )
    )

    first = asyncio.run(
        system.run("Increase Nike Spring Sale campaign budget", thread_id="write-1")
    )
    assert first["intent"] == "write"
    assert first["proposed_action"]["tool"] == "update_campaign_budget"
    assert first["phase"] == "needs_human"
    assert first["compliance_cleared"] is False
    assert first["primary_object"] == "Campaign__c"
