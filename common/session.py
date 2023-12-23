from __future__ import annotations
from typing import TYPE_CHECKING
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from redis.asyncio import Redis
from common import config
from model import GensimModel
import gensim.models.keyedvectors as word2vec

if TYPE_CHECKING:
    from typing import Any
    import motor.core


def get_mongo() -> motor.core.AgnosticDatabase[Any]:
    return MongoClient(config.mongo).Semantle


def get_redis() -> Redis[Any]:
    return Redis.from_url(config.redis, decode_responses=True, max_connections=10)


def get_model() -> GensimModel:
    return GensimModel(word2vec.KeyedVectors.load("model.mdl").wv)
