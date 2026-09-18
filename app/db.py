"""SQLAlchemy engine/session setup. SQLite DB lives at data/app.db."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DB_PATH = "data/app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


class Base(DeclarativeBase):
    pass


def _migrate_sqlite_schema() -> None:
    """Apply lightweight column renames that create_all() will not do.

    After Sri Lanka localization the ORM expects ``crib_score``; older local
    DBs still have ``cibil_score``. Without this, /applications and /analytics
    return 500 and the UI surfaces a generic failure.
    """
    if not engine.url.get_backend_name().startswith("sqlite"):
        return
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        tables = {r[0] for r in rows}
        if "applications" not in tables:
            return
        cols = {
            r[1]
            for r in conn.execute(text("PRAGMA table_info(applications)")).fetchall()
        }
        if "cibil_score" in cols and "crib_score" not in cols:
            conn.execute(text("ALTER TABLE applications RENAME COLUMN cibil_score TO crib_score"))


def init_db() -> None:
    """Create tables on startup (import models first so metadata is populated)."""
    import app.models_db  # noqa: F401

    Base.metadata.create_all(engine)
    _migrate_sqlite_schema()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
