from pymongo import MongoClient
from redis.client import Redis


from common import config


def get_mongo():
    return MongoClient(config.mongo).Semantle.word2vec


def get_redis():
    return Redis.from_url(config.redis, decode_responses=True)
