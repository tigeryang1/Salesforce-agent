from pathlib import Path
from uuid import uuid4

from salesforce_hybrid_sim.seed_data import SEED_DATA
from salesforce_hybrid_sim.sqlite_store import SQLiteStore


def db_path_for_test() -> Path:
    base = Path(__file__).resolve().parents[1] / "data" / "test_runs"
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{uuid4().hex}.db"
    if path.exists():
        path.unlink()
    return path


def test_seed_and_read_account() -> None:
    db_path = db_path_for_test()
    store = SQLiteStore(db_path)
    store.seed(SEED_DATA)
    account = store.get_account("acct_us_001")
    assert account is not None
    assert account["name"] == "Acme Retail"
    assert account["contacts"]
    assert account["opportunities"]
    assert account["campaigns"]


def test_projection_bundle_contains_expected_sections() -> None:
    db_path = db_path_for_test()
    store = SQLiteStore(db_path)
    store.seed(SEED_DATA)
    bundle = store.projection_bundle()
    assert bundle["accounts"]
    assert bundle["contacts"]
    assert bundle["campaign_influence"]
