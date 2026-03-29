from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class Settings:
    sqlite_path: Path
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    neo4j_database: str


def get_settings() -> Settings:
    sqlite_path = Path(os.getenv("SQLITE_PATH", "./data/salesforce.db"))
    if not sqlite_path.is_absolute():
        sqlite_path = PROJECT_ROOT / sqlite_path

    return Settings(
        sqlite_path=sqlite_path,
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_username=os.getenv("NEO4J_USERNAME", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", ""),
        neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
    )

