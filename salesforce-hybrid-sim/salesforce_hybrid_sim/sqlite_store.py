from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


SCHEMA_SQL = [
    "CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY, name TEXT NOT NULL, industry TEXT, region TEXT, tier TEXT, status TEXT)",
    "CREATE TABLE IF NOT EXISTS contacts (id TEXT PRIMARY KEY, account_id TEXT NOT NULL, first_name TEXT, last_name TEXT, email TEXT, title TEXT, FOREIGN KEY(account_id) REFERENCES accounts(id))",
    "CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT, region TEXT)",
    "CREATE TABLE IF NOT EXISTS opportunities (id TEXT PRIMARY KEY, account_id TEXT NOT NULL, owner_user_id TEXT, name TEXT NOT NULL, stage TEXT, amount REAL, close_date TEXT, status TEXT, FOREIGN KEY(account_id) REFERENCES accounts(id), FOREIGN KEY(owner_user_id) REFERENCES users(id))",
    "CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, account_id TEXT NOT NULL, owner_user_id TEXT, subject TEXT NOT NULL, priority TEXT, status TEXT, opened_at TEXT, FOREIGN KEY(account_id) REFERENCES accounts(id), FOREIGN KEY(owner_user_id) REFERENCES users(id))",
    "CREATE TABLE IF NOT EXISTS campaigns (id TEXT PRIMARY KEY, account_id TEXT NOT NULL, name TEXT NOT NULL, status TEXT, budget REAL, channel TEXT, FOREIGN KEY(account_id) REFERENCES accounts(id))",
    "CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, subject TEXT NOT NULL, status TEXT, due_date TEXT, opportunity_id TEXT, case_id TEXT, FOREIGN KEY(opportunity_id) REFERENCES opportunities(id), FOREIGN KEY(case_id) REFERENCES cases(id))",
    "CREATE TABLE IF NOT EXISTS campaign_influence (campaign_id TEXT NOT NULL, opportunity_id TEXT NOT NULL, PRIMARY KEY (campaign_id, opportunity_id))",
    "CREATE TABLE IF NOT EXISTS opportunity_contacts (opportunity_id TEXT NOT NULL, contact_id TEXT NOT NULL, PRIMARY KEY (opportunity_id, contact_id))",
    "CREATE TABLE IF NOT EXISTS account_hierarchy (parent_account_id TEXT NOT NULL, child_account_id TEXT NOT NULL, PRIMARY KEY (parent_account_id, child_account_id))",
]


class SQLiteStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self.connect() as conn:
            for statement in SCHEMA_SQL:
                conn.execute(statement)
            conn.commit()

    def reset(self) -> None:
        with self.connect() as conn:
            for table in ["account_hierarchy", "opportunity_contacts", "campaign_influence", "tasks", "campaigns", "cases", "opportunities", "users", "contacts", "accounts"]:
                conn.execute(f"DELETE FROM {table}")
            conn.commit()

    def seed(self, seed_data: dict[str, list[dict[str, Any]]]) -> None:
        self.init_schema()
        self.reset()
        with self.connect() as conn:
            for table, rows in seed_data.items():
                if not rows:
                    continue
                columns = list(rows[0].keys())
                placeholders = ", ".join(f":{col}" for col in columns)
                conn.executemany(
                    f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                    rows,
                )
            conn.commit()

    def _list(self, query: str, **params: Any) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(query, params)]

    def _one(self, query: str, **params: Any) -> dict[str, Any] | None:
        rows = self._list(query, **params)
        return rows[0] if rows else None

    def health(self) -> dict[str, Any]:
        with self.connect() as conn:
            conn.execute("SELECT 1")
        return {"sqlite": "ok"}

    def get_accounts(self) -> list[dict[str, Any]]:
        return self._list("SELECT * FROM accounts ORDER BY name")

    def get_account_contacts(self, account_id: str) -> list[dict[str, Any]]:
        return self._list(
            "SELECT id, account_id, first_name, last_name, email, title, first_name || ' ' || last_name AS name FROM contacts WHERE account_id = :account_id ORDER BY first_name, last_name",
            account_id=account_id,
        )

    def get_account_opportunities(self, account_id: str) -> list[dict[str, Any]]:
        return self._list(
            "SELECT o.*, u.name AS owner_name, u.role AS owner_role FROM opportunities o LEFT JOIN users u ON u.id = o.owner_user_id WHERE o.account_id = :account_id ORDER BY o.name",
            account_id=account_id,
        )

    def get_account_cases(self, account_id: str) -> list[dict[str, Any]]:
        return self._list(
            "SELECT c.*, u.name AS owner_name, u.role AS owner_role FROM cases c LEFT JOIN users u ON u.id = c.owner_user_id WHERE c.account_id = :account_id ORDER BY c.opened_at DESC",
            account_id=account_id,
        )

    def get_account_campaigns(self, account_id: str) -> list[dict[str, Any]]:
        return self._list("SELECT * FROM campaigns WHERE account_id = :account_id ORDER BY name", account_id=account_id)

    def get_account(self, account_id: str) -> dict[str, Any] | None:
        account = self._one("SELECT * FROM accounts WHERE id = :account_id", account_id=account_id)
        if account is None:
            return None
        account["contacts"] = self.get_account_contacts(account_id)
        account["opportunities"] = self.get_account_opportunities(account_id)
        account["cases"] = self.get_account_cases(account_id)
        account["campaigns"] = self.get_account_campaigns(account_id)
        return account

    def get_opportunities(self) -> list[dict[str, Any]]:
        return self._list("SELECT o.*, a.name AS account_name, u.name AS owner_name, u.role AS owner_role FROM opportunities o JOIN accounts a ON a.id = o.account_id LEFT JOIN users u ON u.id = o.owner_user_id ORDER BY o.name")

    def get_cases(self) -> list[dict[str, Any]]:
        return self._list("SELECT c.*, a.name AS account_name, u.name AS owner_name, u.role AS owner_role FROM cases c JOIN accounts a ON a.id = c.account_id LEFT JOIN users u ON u.id = c.owner_user_id ORDER BY c.opened_at DESC")

    def get_campaigns(self) -> list[dict[str, Any]]:
        return self._list("SELECT c.*, a.name AS account_name FROM campaigns c JOIN accounts a ON a.id = c.account_id ORDER BY c.name")

    def projection_bundle(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "accounts": self.get_accounts(),
            "contacts": self._list("SELECT id, account_id, first_name, last_name, email, title, first_name || ' ' || last_name AS name FROM contacts"),
            "users": self._list("SELECT * FROM users"),
            "opportunities": self._list("SELECT * FROM opportunities"),
            "cases": self._list("SELECT * FROM cases"),
            "campaigns": self._list("SELECT * FROM campaigns"),
            "tasks": self._list("SELECT * FROM tasks"),
            "campaign_influence": self._list("SELECT * FROM campaign_influence"),
            "opportunity_contacts": self._list("SELECT * FROM opportunity_contacts"),
            "account_hierarchy": self._list("SELECT * FROM account_hierarchy"),
        }

