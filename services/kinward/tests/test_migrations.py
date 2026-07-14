from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
import pytest
from sqlalchemy import create_engine, text

from kinward.config import get_settings
from kinward.health import EXPECTED_SCHEMA_REVISION


def test_initial_migration_is_the_only_root_and_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service_root = Path(__file__).parents[1]
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"
    monkeypatch.setenv("KINWARD_DATABASE_URL", database_url)
    get_settings.cache_clear()
    config = Config(str(service_root / "alembic.ini"))
    config.set_main_option("script_location", str(service_root / "migrations"))
    script = ScriptDirectory.from_config(config)

    revisions = list(script.walk_revisions())
    assert len(revisions) == 1
    assert revisions[0].revision == EXPECTED_SCHEMA_REVISION
    assert revisions[0].down_revision is None

    command.upgrade(config, "head")
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            EXPECTED_SCHEMA_REVISION
        )
        tables = {
            row[0]
            for row in connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'table'")
            )
        }
    assert {"outbox_messages", "worker_heartbeats"} <= tables
    engine.dispose()
    get_settings.cache_clear()
