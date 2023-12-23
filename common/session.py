from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from redis.asyncio import Redis
from common.logger import logger
from common import config
from model import GensimModel
import gensim.models.keyedvectors as word2vec


def get_mongo():
    return MongoClient(config.mongo).Semantle


def get_redis():
    return Redis.from_url(config.redis, decode_responses=True, max_connections=10)


def get_model():
    return GensimModel(word2vec.KeyedVectors.load("model.mdl").wv)
