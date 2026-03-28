from __future__ import annotations

import logging
import os
import pickle
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from agents.context import AgentContext
from agents.system import SalesforceAgentSystem, build_agent_system


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "agent_state.db"
logger = logging.getLogger(__name__)


class AgentSystemRegistry:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(db_path or os.getenv("AGENT_STATE_DB", str(DEFAULT_DB_PATH)))
        self._systems: dict[str, SalesforceAgentSystem] = {}
        self._metadata: dict[str, dict] = {}
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_state (
                    thread_id TEXT PRIMARY KEY,
                    session_token TEXT NOT NULL,
                    mcp_url TEXT NOT NULL,
                    model TEXT NOT NULL,
                    context_json BLOB NOT NULL,
                    checkpoint_blob BLOB NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    async def create_or_replace(
        self,
        *,
        thread_id: str,
        session_token: str,
        mcp_url: str,
        model: str,
        agent_context: AgentContext,
    ) -> SalesforceAgentSystem:
        system = await build_agent_system(
            session_token=session_token,
            mcp_url=mcp_url,
            model=model,
            agent_context=agent_context,
        )
        self._systems[thread_id] = system
        self._metadata[thread_id] = {
            "session_token": session_token,
            "mcp_url": mcp_url,
            "model": model,
            "agent_context": agent_context,
        }
        self.save(thread_id)
        return system

    async def get(self, thread_id: str) -> SalesforceAgentSystem | None:
        if thread_id in self._systems:
            return self._systems[thread_id]

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT session_token, mcp_url, model, context_json, checkpoint_blob
                FROM workflow_state
                WHERE thread_id = ?
                """,
                (thread_id,),
            ).fetchone()

        if row is None:
            return None

        session_token, mcp_url, model, context_blob, checkpoint_blob = row
        context = pickle.loads(context_blob)
        checkpointer = None
        if checkpoint_blob:
            try:
                checkpointer = pickle.loads(checkpoint_blob)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to restore checkpoint for thread %s: %s", thread_id, exc)
        system = await build_agent_system(
            session_token=session_token,
            mcp_url=mcp_url,
            model=model,
            agent_context=context,
            checkpointer=checkpointer,
        )
        self._systems[thread_id] = system
        self._metadata[thread_id] = {
            "session_token": session_token,
            "mcp_url": mcp_url,
            "model": model,
            "agent_context": context,
        }
        return system

    def save(self, thread_id: str) -> None:
        system = self._systems[thread_id]
        metadata = self._metadata[thread_id]
        context_blob = pickle.dumps(metadata["agent_context"])
        checkpoint_blob: bytes = b""
        try:
            checkpoint_blob = pickle.dumps(system.checkpointer)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Checkpoint persistence disabled for thread %s because the checkpointer is not picklable: %s",
                thread_id,
                exc,
            )
        updated_at = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_state (
                    thread_id, session_token, mcp_url, model, context_json, checkpoint_blob, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                    session_token=excluded.session_token,
                    mcp_url=excluded.mcp_url,
                    model=excluded.model,
                    context_json=excluded.context_json,
                    checkpoint_blob=excluded.checkpoint_blob,
                    updated_at=excluded.updated_at
                """,
                (
                    thread_id,
                    metadata["session_token"],
                    metadata["mcp_url"],
                    metadata["model"],
                    context_blob,
                    checkpoint_blob,
                    updated_at,
                ),
            )
            conn.commit()


def ensure_model_key(model: str) -> None:
    if model.startswith("gemini:") and not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY is required when using a Gemini model.")
    if model.startswith("openai:") and not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is required when using an OpenAI model.")


def ensure_openai_key(model: str) -> None:
    ensure_model_key(model)


def serialize_context(context: AgentContext) -> dict:
    return asdict(context)


def get_api_token() -> str:
    token = os.getenv("AGENT_API_TOKEN")
    if not token:
        raise ValueError("AGENT_API_TOKEN must be set for API authentication.")
    return token
