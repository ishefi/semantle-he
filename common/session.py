from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from aioredis.client import Redis
from common.logger import logger
from common import config
from model import GensimModel


def get_mongo():
    return MongoClient(config.mongo).Semantle


def get_redis():
    return Redis.from_url(config.redis, decode_responses=True, max_connections=10)


def get_model(mongo=None, has_model=False):
    if has_model is not None:
        logger.info("using model")
        import gensim.models.keyedvectors as word2vec
        return GensimModel(word2vec.KeyedVectors.load("model.mdl").wv)
    raise Exception('couldnt find model')
