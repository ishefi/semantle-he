from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

import gensim.models.keyedvectors as word2vec
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from redis.asyncio import Redis
from sqlmodel import Session
from sqlmodel import create_engine

from common import config
from model import GensimModel

if TYPE_CHECKING:
    from typing import Any
    from typing import Iterator

    import motor.core


def get_mongo() -> motor.core.AgnosticDatabase[Any]:
    return MongoClient(config.mongo).Semantle


def get_redis() -> Redis[Any]:
    return Redis.from_url(config.redis, decode_responses=True, max_connections=10)


def get_model() -> GensimModel:
    return GensimModel(word2vec.KeyedVectors.load("model.mdl").wv)


def get_session() -> Session:
    engine = create_engine(config.db_url)
    return Session(engine)


@contextmanager
def hs_transaction(session: Session) -> Iterator[Session]:
    try:
        session.begin()
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
