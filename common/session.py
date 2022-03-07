from datetime import datetime

from pymongo import MongoClient
from redis.client import Redis


from common import config


def get_mongo():
    mongdb = MongoClient(config.mongo).Semantle
    if str(datetime.utcnow().date()) >= config.model_v2_date:
        return mongdb.word2vec2
    else:
        return mongdb.word2vec


def get_redis():
    return Redis.from_url(config.redis, decode_responses=True)
