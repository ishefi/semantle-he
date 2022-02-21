from __future__ import annotations

from datetime import timedelta
import heapq
import struct
from typing import TYPE_CHECKING


from common.consts import VEC_SIZE
from common.tables import Word2Vec

from numpy import dot
from numpy.linalg import norm

from datetime import datetime
if TYPE_CHECKING:
    from typing import Optional
    from datetime import date


class SecretLogic:

    def __init__(self, session_factory, dt: Optional[date] = None) -> None:
        if dt is None:
            dt = datetime.utcnow().date()
        self.date = dt
        self.session_factory = session_factory

    def get_secret(self):
        query = self.session_factory().query(Word2Vec)
        query = query.filter(Word2Vec.secret_date == self.date)
        wv = query.one_or_none()
        if wv:
            return wv.word
        else:
            return None

    def set_secret(self, secret):
        session = self.session_factory()
        wv = session.query(Word2Vec).filter(Word2Vec.word == secret).one()
        session.begin()
        wv.secret_date = self.date
        session.add(wv)
        session.commit()


class VectorLogic:
    def __init__(self, session_factory, dt=None):
        self.session_factory = session_factory
        self.secret_logic = SecretLogic(self.session_factory, dt=dt)

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
        if dt is None:
            dt = datetime.utcnow().date()
        self.date = str(dt)
        self.vector_logic = VectorLogic(self.session_factory, dt=dt)
        self.secret = secret
        self._cache = None

    @property
    def secret_cache_key(self):
        return self._secret_cache_key.format(self.secret, self.date)

    def set_secret(self, dry=False):
        if self.vector_logic.secret_logic.get_secret() is not None:
            raise ValueError("There is already a secret for this date")

        query = self.session_factory().query(Word2Vec)
        wv = query.filter(Word2Vec.word == self.secret).one()
        if wv.secret_date is not None:
            raise ValueError("This word was a secret in the past")

        target_vec = self.vector_logic.get_vector(self.secret)

        nearest = []
        for word, vec in self.vector_logic.iterate_all():
            s = self.vector_logic.calc_similarity(vec, target_vec)
            heapq.heappush(nearest, (s, word))
            if len(nearest) > 1000:
                heapq.heappop(nearest)
        nearest.sort()
        if not dry:
            self.redis.rpush(self.secret_cache_key, *[w[1] for w in nearest])
            self.redis.expire(self.secret_cache_key, timedelta(hours=96))
            self.vector_logic.secret_logic.set_secret(self.secret)
        else:
            self._cache = nearest

    @property
    def cache(self):
        if self._cache is None:
            self._cache = self.redis.lrange(self.secret_cache_key, 0, -1)
        return self._cache

    def get_cache_score(self, word):
        try:
            return self.cache.index(word) + 1
        except ValueError:
            return -1
