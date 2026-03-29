from neo4j_setup.schema import SCHEMA_STATEMENTS
from neo4j_setup.seed import load_seed_data


def test_schema_statements_include_account_constraint() -> None:
    assert any("account_id" in statement for statement in SCHEMA_STATEMENTS)


def test_sample_graph_contains_salesforce_objects_and_relationships() -> None:
    data = load_seed_data()
    assert data["accounts"]
    assert data["contacts"]
    assert data["opportunities"]
    assert data["cases"]
    assert data["campaigns"]
    assert data["users"]
    assert data["tasks"]
    assert data["campaign_influence"]
    assert data["opportunity_contacts"]
    assert data["account_hierarchy"]
    assert data["contacts"][0]["account_id"]
    assert data["opportunities"][0]["owner_user_id"]
