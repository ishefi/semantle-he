from __future__ import annotations

import heapq
import struct
from typing import TYPE_CHECKING


from common.consts import VEC_SIZE
from common.tables import Word2Vec

from numpy import dot
from numpy.linalg import norm

from datetime import datetime
if TYPE_CHECKING:
    from redis import Redis
    from typing import Optional


class SecretLogic:
    _secret_key = 'hs:secret:{}'

    def __init__(self, session_factory, redis: Redis, dt: Optional[datetime] = None) -> None:
        self.redis = redis
        if dt is None:
            dt = datetime.utcnow().date()
        self.date = str(dt)
        self.session_factory = session_factory

    @property
    def secret_key(self):
        return self._secret_key.format(self.date)

    def get_secret(self):
        return self.redis.get(self.secret_key)

    def set_secret(self, secret):
        return self.redis.set(self.secret_key, secret)


class VectorLogic:
    def __init__(self, session_factory, redis):
        self.session_factory = session_factory
        self.redis = redis
        self.secret_logic = SecretLogic(self.session_factory, self.redis)

    def get_vector(self, word: str):
        session = self.session_factory()
        query = session.query(Word2Vec.vec)
        query = query.filter(Word2Vec.word == word)
        raw_vec = query.one_or_none()
        if raw_vec is None:
            return None
        else:
            return self._unpack_vector(raw_vec.vec)

    def _unpack_vector(self, raw_vec):
        return struct.unpack(VEC_SIZE, raw_vec)

    def get_similarity(self, word: str) -> float:
        word_vector = self.get_vector(word)
        if word_vector is None:
            return -1.0
        secret_vector = self.get_vector(self.secret_logic.get_secret())
        return self.calc_similarity(secret_vector, word_vector)

    def calc_similarity(self, vec1, vec2):
        return round(abs(
            dot(vec1, vec2) / (norm(vec1) * norm(vec2))
        ) * 100, 2)

    def iterate_all(self) -> [Word2Vec]:
        session = self.session_factory()
        query = session.query(Word2Vec)
        for wv in query:
            yield wv.word, self._unpack_vector(wv.vec)


class CacheSecretLogic:
    _secret_cache_key = 'hs:{}:{}'

    def __init__(self, session_factory, redis, secret, dt):
        self.session_factory = session_factory
        self.redis = redis
        self.vector_logic = VectorLogic(self.session_factory, self.redis)
        self.secret = secret
        if dt is None:
            dt = datetime.utcnow().date()
        self.date = str(dt)
        self._cache = None

    @property
    def secret_cache_key(self):
        return self._secret_cache_key.format(self.secret, self.date)

    def set_secret(self):
        target_vec = self.vector_logic.get_vector(self.secret)
        nearest = []
        for word, vec in self.vector_logic.iterate_all():
            s = self.vector_logic.calc_similarity(vec, target_vec)
            heapq.heappush(nearest, (s, word))
            if len(nearest) > 1000:
                heapq.heappop(nearest)
        nearest.sort()
        self.redis.rpush(self.secret_cache_key, *[w[1] for w in nearest])
        self.vector_logic.secret_logic.set_secret(self.secret)

    @property
    def cache(self):
        if self._cache is None:
            self._cache = self.redis.lrange(self.secret_cache_key, 0, -1)
        return self._cache

    def get_cache_score(self, word):
        try:
            return self.cache.index(word)
        except ValueError:
            return -1

