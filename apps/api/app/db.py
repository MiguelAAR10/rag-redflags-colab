"""SQLModel engine and session helpers."""

from __future__ import annotations

from sqlmodel import SQLModel, Session, create_engine

from .config import get_settings


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            settings.database_url,
            connect_args=connect_args,
            echo=False,
        )
    return _engine


def init_db() -> None:
    """Create tables if they do not exist."""
    from . import models  # noqa: F401  ensure models are registered

    SQLModel.metadata.create_all(get_engine())


def get_session() -> Session:
    return Session(get_engine())