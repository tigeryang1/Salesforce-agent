from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_FILE = PROJECT_ROOT / "data" / "sample_graph.json"


NODE_MERGE_QUERIES = {
    "accounts": """
        MERGE (n:Account {id: $row.id})
        SET n.name = $row.name,
            n.industry = $row.industry,
            n.region = $row.region,
            n.tier = $row.tier,
            n.status = $row.status
    """.strip(),
    "contacts": """
        MERGE (n:Contact {id: $row.id})
        SET n.first_name = $row.first_name,
            n.last_name = $row.last_name,
            n.email = $row.email,
            n.title = $row.title,
            n.account_id = $row.account_id,
            n.name = $row.first_name + ' ' + $row.last_name
    """.strip(),
    "opportunities": """
        MERGE (n:Opportunity {id: $row.id})
        SET n.name = $row.name,
            n.account_id = $row.account_id,
            n.owner_user_id = $row.owner_user_id,
            n.stage = $row.stage,
            n.amount = $row.amount,
            n.close_date = $row.close_date,
            n.status = $row.status
    """.strip(),
    "cases": """
        MERGE (n:Case {id: $row.id})
        SET n.subject = $row.subject,
            n.account_id = $row.account_id,
            n.owner_user_id = $row.owner_user_id,
            n.priority = $row.priority,
            n.status = $row.status,
            n.opened_at = $row.opened_at
    """.strip(),
    "campaigns": """
        MERGE (n:Campaign {id: $row.id})
        SET n.name = $row.name,
            n.account_id = $row.account_id,
            n.status = $row.status,
            n.budget = $row.budget,
            n.channel = $row.channel
    """.strip(),
    "users": """
        MERGE (n:User {id: $row.id})
        SET n.name = $row.name,
            n.role = $row.role,
            n.region = $row.region
    """.strip(),
    "tasks": """
        MERGE (n:Task {id: $row.id})
        SET n.subject = $row.subject,
            n.status = $row.status,
            n.due_date = $row.due_date,
            n.opportunity_id = $row.opportunity_id,
            n.case_id = $row.case_id
    """.strip(),
}


def load_seed_data(data_file: Path | None = None) -> dict[str, Any]:
    target = Path(data_file) if data_file else DEFAULT_DATA_FILE
    return json.loads(target.read_text(encoding="utf-8"))


def reset_graph(driver, database: str) -> None:
    with driver.session(database=database) as session:
        session.run("MATCH (n) DETACH DELETE n").consume()


def seed_nodes(driver, database: str, seed_data: dict[str, Any]) -> None:
    with driver.session(database=database) as session:
        for section, query in NODE_MERGE_QUERIES.items():
            for row in seed_data.get(section, []):
                session.run(query, row=row).consume()


def seed_relationships(driver, database: str, seed_data: dict[str, Any]) -> None:
    with driver.session(database=database) as session:
        for row in seed_data.get("contacts", []):
            session.run(
                """
                MATCH (c:Contact {id: $contact_id})
                MATCH (a:Account {id: $account_id})
                MERGE (c)-[:WORKS_FOR]->(a)
                """.strip(),
                contact_id=row["id"],
                account_id=row["account_id"],
            ).consume()

        for row in seed_data.get("opportunities", []):
            session.run(
                """
                MATCH (o:Opportunity {id: $opportunity_id})
                MATCH (a:Account {id: $account_id})
                MERGE (o)-[:FOR_ACCOUNT]->(a)
                """.strip(),
                opportunity_id=row["id"],
                account_id=row["account_id"],
            ).consume()
            if row.get("owner_user_id"):
                session.run(
                    """
                    MATCH (u:User {id: $user_id})
                    MATCH (o:Opportunity {id: $opportunity_id})
                    MERGE (u)-[:OWNS]->(o)
                    """.strip(),
                    user_id=row["owner_user_id"],
                    opportunity_id=row["id"],
                ).consume()

        for row in seed_data.get("cases", []):
            session.run(
                """
                MATCH (c:Case {id: $case_id})
                MATCH (a:Account {id: $account_id})
                MERGE (c)-[:FOR_ACCOUNT]->(a)
                """.strip(),
                case_id=row["id"],
                account_id=row["account_id"],
            ).consume()
            if row.get("owner_user_id"):
                session.run(
                    """
                    MATCH (u:User {id: $user_id})
                    MATCH (c:Case {id: $case_id})
                    MERGE (u)-[:OWNS]->(c)
                    """.strip(),
                    user_id=row["owner_user_id"],
                    case_id=row["id"],
                ).consume()

        for row in seed_data.get("campaigns", []):
            session.run(
                """
                MATCH (c:Campaign {id: $campaign_id})
                MATCH (a:Account {id: $account_id})
                MERGE (c)-[:TARGETS]->(a)
                """.strip(),
                campaign_id=row["id"],
                account_id=row["account_id"],
            ).consume()

        for row in seed_data.get("account_hierarchy", []):
            session.run(
                """
                MATCH (p:Account {id: $parent_account_id})
                MATCH (c:Account {id: $child_account_id})
                MERGE (p)-[:PARENT_OF]->(c)
                """.strip(),
                parent_account_id=row["parent_account_id"],
                child_account_id=row["child_account_id"],
            ).consume()

        for row in seed_data.get("campaign_influence", []):
            session.run(
                """
                MATCH (c:Campaign {id: $campaign_id})
                MATCH (o:Opportunity {id: $opportunity_id})
                MERGE (c)-[:INFLUENCED]->(o)
                """.strip(),
                campaign_id=row["campaign_id"],
                opportunity_id=row["opportunity_id"],
            ).consume()

        for row in seed_data.get("opportunity_contacts", []):
            session.run(
                """
                MATCH (o:Opportunity {id: $opportunity_id})
                MATCH (c:Contact {id: $contact_id})
                MERGE (o)-[:INVOLVES_CONTACT]->(c)
                """.strip(),
                opportunity_id=row["opportunity_id"],
                contact_id=row["contact_id"],
            ).consume()

        for row in seed_data.get("tasks", []):
            if row.get("opportunity_id"):
                session.run(
                    """
                    MATCH (t:Task {id: $task_id})
                    MATCH (o:Opportunity {id: $opportunity_id})
                    MERGE (t)-[:RELATED_TO]->(o)
                    """.strip(),
                    task_id=row["id"],
                    opportunity_id=row["opportunity_id"],
                ).consume()
            if row.get("case_id"):
                session.run(
                    """
                    MATCH (t:Task {id: $task_id})
                    MATCH (c:Case {id: $case_id})
                    MERGE (t)-[:RELATED_TO]->(c)
                    """.strip(),
                    task_id=row["id"],
                    case_id=row["case_id"],
                ).consume()


def seed_graph(driver, database: str, seed_data: dict[str, Any]) -> None:
    seed_nodes(driver, database, seed_data)
    seed_relationships(driver, database, seed_data)


def verify_graph(driver, database: str) -> dict[str, int]:
    query = """
    RETURN
      size([(n:Account) | n]) AS accounts,
      size([(n:Contact) | n]) AS contacts,
      size([(n:Opportunity) | n]) AS opportunities,
      size([(n:Case) | n]) AS cases,
      size([(n:Campaign) | n]) AS campaigns,
      size([(n:User) | n]) AS users,
      size([(n:Task) | n]) AS tasks,
      size([()-->() | 1]) AS relationships
    """.strip()
    with driver.session(database=database) as session:
        record = session.run(query).single()
        return dict(record.items()) if record else {}
