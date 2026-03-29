from __future__ import annotations

SCHEMA_STATEMENTS = [
    """
    CREATE CONSTRAINT account_id IF NOT EXISTS
    FOR (n:Account)
    REQUIRE n.id IS UNIQUE
    """.strip(),
    """
    CREATE CONSTRAINT contact_id IF NOT EXISTS
    FOR (n:Contact)
    REQUIRE n.id IS UNIQUE
    """.strip(),
    """
    CREATE CONSTRAINT opportunity_id IF NOT EXISTS
    FOR (n:Opportunity)
    REQUIRE n.id IS UNIQUE
    """.strip(),
    """
    CREATE CONSTRAINT case_id IF NOT EXISTS
    FOR (n:Case)
    REQUIRE n.id IS UNIQUE
    """.strip(),
    """
    CREATE CONSTRAINT campaign_id IF NOT EXISTS
    FOR (n:Campaign)
    REQUIRE n.id IS UNIQUE
    """.strip(),
    """
    CREATE CONSTRAINT user_id IF NOT EXISTS
    FOR (n:User)
    REQUIRE n.id IS UNIQUE
    """.strip(),
    """
    CREATE CONSTRAINT task_id IF NOT EXISTS
    FOR (n:Task)
    REQUIRE n.id IS UNIQUE
    """.strip(),
    """
    CREATE INDEX account_name IF NOT EXISTS
    FOR (n:Account)
    ON (n.name)
    """.strip(),
    """
    CREATE INDEX contact_email IF NOT EXISTS
    FOR (n:Contact)
    ON (n.email)
    """.strip(),
    """
    CREATE INDEX opportunity_name IF NOT EXISTS
    FOR (n:Opportunity)
    ON (n.name)
    """.strip(),
    """
    CREATE INDEX campaign_name IF NOT EXISTS
    FOR (n:Campaign)
    ON (n.name)
    """.strip(),
]


def apply_schema(driver, database: str) -> None:
    with driver.session(database=database) as session:
        for statement in SCHEMA_STATEMENTS:
            session.run(statement).consume()

