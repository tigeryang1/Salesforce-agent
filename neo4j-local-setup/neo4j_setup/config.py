from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Neo4jSettings:
    uri: str
    username: str
    password: str
    database: str


def get_settings() -> Neo4jSettings:
    password = os.getenv("NEO4J_PASSWORD", "")
    if not password:
        raise ValueError("Missing NEO4J_PASSWORD. Set it in your environment or a .env file.")

    return Neo4jSettings(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=password,
        database=os.getenv("NEO4J_DATABASE", "neo4j"),
    )

