from app.datastore import DataStore
from app.utility.errors import MCPError
from app.operation.discover import DiscoveryService
from app.operation.tools import ToolsService


def build_tools() -> ToolsService:
    return ToolsService(DataStore())


def build_discovery() -> DiscoveryService:
    return DiscoveryService(DataStore())


def test_search_advertiser_disambiguation() -> None:
    discovery = build_discovery()
    try:
        discovery.search_advertiser("tok_alice_us", "Nike")
        assert False, "Expected disambiguation error"
    except MCPError as err:
        assert err.code == "ENTITY_DISAMBIGUATION_REQUIRED"
        assert len(err.details["candidates"]) >= 2


def test_search_global_ranked_results() -> None:
    discovery = build_discovery()
    result = discovery.search_global("tok_alice_us", "spring", limit=5)
    assert result["count"] >= 1
    assert result["results"][0]["confidence"] >= result["results"][-1]["confidence"]


def test_resolve_company_context_returns_ranked_objects() -> None:
    discovery = build_discovery()
    result = discovery.resolve_company_context("tok_alice_us", "Show me Nike US deals and pipeline")
    assert result["entity_id"] == "acct_us_001"
    assert result["primary_object"] == "Opportunity"
    assert "Account" in result["related_objects"]
    assert result["candidates"][0]["score"] >= result["candidates"][1]["score"]


def test_resolve_company_context_requires_clarification_for_broad_query() -> None:
    discovery = build_discovery()
    result = discovery.resolve_company_context("tok_alice_us", "Tell me about Acme Advertising")
    assert result["entity_id"] == "acct_us_002"
    assert result["needs_clarification"] is True
    assert result["clarification_question"]


def test_create_support_case_success() -> None:
    tools = build_tools()
    result = tools.create_support_case(
        "tok_alice_us", "acct_us_001", "Need help", "High", "Investigate spend gap"
    )
    assert result["account_id"] == "acct_us_001"
    assert result["priority"] == "High"


def test_update_campaign_budget_requires_approval() -> None:
    tools = build_tools()
    try:
        tools.update_campaign_budget(
            token="tok_alice_us",
            campaign_id="camp_us_001",
            new_budget=150000,
            idempotency_key="idem_1",
        )
        assert False, "Expected approval-required error"
    except MCPError as err:
        assert err.code == "APPROVAL_REQUIRED"
        assert "review_packet_id" in err.details


def test_update_campaign_budget_with_approval() -> None:
    tools = build_tools()

    packet_id = None
    approval_token = None
    try:
        tools.update_campaign_budget(
            token="tok_alice_us",
            campaign_id="camp_us_001",
            new_budget=150000,
            idempotency_key="idem_2",
        )
    except MCPError as err:
        packet_id = err.details["review_packet_id"]
        approval_token = tools.store.approval_packets[packet_id]["approval_token"]

    result = tools.update_campaign_budget(
        token="tok_alice_us",
        campaign_id="camp_us_001",
        new_budget=150000,
        idempotency_key="idem_2",
        review_packet_id=packet_id,
        approval_token=approval_token,
    )
    assert result["updated"] is True
    assert result["new_budget"] == 150000


def test_optimize_campaign_returns_job_payload() -> None:
    tools = build_tools()
    result = tools.optimize_campaign("tok_alice_us", "acct_us_001", "idem_job_1")
    assert result["status"] == "queued"
    assert result["job_id"].startswith("job_")
