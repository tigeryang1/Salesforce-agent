from __future__ import annotations

from neo4j_setup.config import Neo4jSettings


def build_driver(settings: Neo4jSettings):
    from neo4j import GraphDatabase

    return GraphDatabase.driver(settings.uri, auth=(settings.username, settings.password))

