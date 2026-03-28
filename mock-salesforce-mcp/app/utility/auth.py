from __future__ import annotations

from app.datastore import DataStore
from app.utility.errors import auth_expired
from app.models import Session


def get_session(store: DataStore, token: str) -> Session:
    session = store.sessions.get(token)
    if not session or session.auth_state in {"expired", "revoked"}:
        raise auth_expired()
    return session

