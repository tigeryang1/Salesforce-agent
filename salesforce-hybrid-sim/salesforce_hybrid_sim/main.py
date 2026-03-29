from __future__ import annotations

import argparse

from salesforce_hybrid_sim.config import get_settings
from salesforce_hybrid_sim.neo4j_projector import Neo4jProjector
from salesforce_hybrid_sim.seed_data import SEED_DATA
from salesforce_hybrid_sim.sqlite_store import SQLiteStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the Salesforce hybrid simulator")
    parser.add_argument("--init-db", action="store_true")
    parser.add_argument("--seed", action="store_true")
    parser.add_argument("--sync-graph", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    store = SQLiteStore(settings.sqlite_path)
    if args.init_db:
        store.init_schema()
        print("SQLite schema initialized.")
    if args.seed:
        store.seed(SEED_DATA)
        print("SQLite seeded.")
    if args.sync_graph:
        projector = Neo4jProjector(settings.neo4j_uri, settings.neo4j_username, settings.neo4j_password, settings.neo4j_database)
        print("Graph sync:", projector.sync_all(store.projection_bundle()))


if __name__ == "__main__":
    main()

