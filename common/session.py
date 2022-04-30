from motor.motor_asyncio import AsyncIOMotorClient as MongoClient

from aioredis.client import Redis


from common import config


def get_mongo():
    mongdb = MongoClient(config.mongo).Semantle
    return mongdb.word2vec2


def get_redis():
    return Redis.from_url(config.redis, decode_responses=True)
