from __future__ import annotations

import argparse

from neo4j_setup.config import get_settings
from neo4j_setup.db import build_driver
from neo4j_setup.schema import apply_schema
from neo4j_setup.seed import load_seed_data, reset_graph, seed_graph, verify_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up schema and sample data in local Neo4j")
    parser.add_argument("--reset", action="store_true", help="Delete all nodes and relationships first")
    parser.add_argument("--schema-only", action="store_true", help="Apply schema only")
    parser.add_argument("--data-file", default=None, help="Optional path to seed data JSON")
    args = parser.parse_args()

    settings = get_settings()
    driver = build_driver(settings)
    try:
        if args.reset:
            reset_graph(driver, settings.database)
            print("Graph reset complete.")

        apply_schema(driver, settings.database)
        print("Schema applied.")

        if not args.schema_only:
            seed_data = load_seed_data(args.data_file)
            seed_graph(driver, settings.database, seed_data)
            print("Sample data loaded.")

        counts = verify_graph(driver, settings.database)
        print("Verification:", counts)
    finally:
        driver.close()


if __name__ == "__main__":
    main()

