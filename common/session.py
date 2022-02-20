from redis.client import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from common import config


def get_session_factory(lite=False):
    if lite:
        url = 'sqlite:///word2vec.db'
    else:
        url = config.db
    return scoped_session(
        sessionmaker(
            bind=create_engine(url),
            autocommit=True,
            expire_on_commit=False,
            autoflush=True,
        )
    )


def get_redis():
    return Redis.from_url(config.redis, decode_responses=True)
