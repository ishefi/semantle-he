from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

import gensim.models.keyedvectors as word2vec
import sqlalchemy
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from redis.asyncio import Redis
from sqlmodel import Session
from sqlmodel import create_engine

from common import config
from model import GensimModel

if TYPE_CHECKING:
    import sqlite3
    from typing import Any
    from typing import Iterator

    import motor.core


def get_mongo() -> motor.core.AgnosticDatabase[Any]:
    return MongoClient(config.mongo).Semantle


def get_redis() -> Redis[Any]:
    return Redis.from_url(config.redis, decode_responses=True, max_connections=10)


def get_model() -> GensimModel:
    return GensimModel(word2vec.KeyedVectors.load("model.mdl").wv)


def _fk_pragma_on_connect(dbapi_con: sqlite3.Connection, _: Any) -> None:
    dbapi_con.execute("PRAGMA foreign_keys=ON")


def get_session() -> Session:
    engine = create_engine(config.db_url)
    sqlalchemy.event.listen(engine, "connect", _fk_pragma_on_connect)
    return Session(engine)


@contextmanager
def hs_transaction(
    session: Session, expire_on_commit: bool = True
) -> Iterator[Session]:
    try:
        if not expire_on_commit:
            session.expire_on_commit = False
        session.begin()
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.expire_on_commit = True
        session.close()
