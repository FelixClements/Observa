from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from plexpy.db.engine import get_engine


_SESSION_FACTORY: Optional[sessionmaker] = None


def init_session_factory(engine: Engine):
    global _SESSION_FACTORY
    _SESSION_FACTORY = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return _SESSION_FACTORY


def get_session_factory():
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _SESSION_FACTORY


def get_session() -> Session:
    return get_session_factory()()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
