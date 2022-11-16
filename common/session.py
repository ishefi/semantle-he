from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from aioredis.client import Redis

from common import config
from model import MongoModel, GensimModel


def get_mongo():
    mongdb = MongoClient(config.mongo).Semantle
    return mongdb.word2vec2


def get_redis():
    return Redis.from_url(config.redis, decode_responses=True)


def get_model(mongo=None, model_path=None):
    if model_path is not None:
        import gensim.models.keyedvectors as word2vec
        return GensimModel(word2vec.KeyedVectors.load(model_path).wv)
    else:
        return MongoModel(mongo)
