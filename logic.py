from __future__ import annotations

from datetime import timedelta
import heapq
import struct
from typing import TYPE_CHECKING

from pymongo.collection import Collection

from common.consts import VEC_SIZE

from numpy import dot
from numpy.linalg import norm

from datetime import datetime
if TYPE_CHECKING:
    from typing import Optional
    from datetime import date


class SecretLogic:

    def __init__(self, mongo, dt: Optional[date] = None) -> None:
        if dt is None:
            dt = datetime.utcnow().date()
        self.date = dt
        self.mongo = mongo

    def get_secret(self):
        wv = self.mongo.find_one({'secret_date': str(self.date)})
        if wv:
            return wv['word']
        else:
            return None

    def set_secret(self, secret):
        self.mongo.update_one(
            {'word': secret},
            {'$set': {'secret_date': str(self.date)}}

        )

    def get_all_secrets(self):
        secrets = self.mongo.find({'secret_date': {'$exists': True, '$ne': None}})
        return ((secret['word'], secret['secret_date']) for secret in secrets)


class VectorLogic:
    _secret_cache = {}

    def __init__(self, mongo, dt):
        self.mongo: Collection = mongo
        self.date = str(dt)
        self.secret_logic = SecretLogic(self.mongo, dt=dt)

    def get_vector(self, word: str):
        w2v = self.mongo.find_one({'word': word})
        if w2v is None:
            return None
        else:
            return self._unpack_vector(w2v['vec'])

    def _unpack_vector(self, raw_vec):
        return struct.unpack(VEC_SIZE, raw_vec)

    def get_similarities(self, words: [str]) -> [float]:
        secret_vector = self.get_secret_vector()
        return {
            wv['word']: self.calc_similarity(secret_vector, self._unpack_vector(wv['vec']))
            for wv in self.mongo.find({'word': {'$in': words}})
        }

    def get_secret_vector(self):
        if self._secret_cache.get(self.date) is None:
            self._secret_cache[self.date] = self.get_vector(
                self.secret_logic.get_secret()
            )
        return self._secret_cache[self.date]

    def get_similarity(self, word: str) -> float:
        word_vector = self.get_vector(word)
        if word_vector is None:
            return -1.0
        secret_vector = self.get_secret_vector()
        return self.calc_similarity(secret_vector, word_vector)

    def calc_similarity(self, vec1, vec2):
        return round(abs(
            dot(vec1, vec2) / (norm(vec1) * norm(vec2))
        ) * 100, 2)

    def iterate_all(self):
        for wv in self.mongo.find():
            yield wv['word'], self._unpack_vector(wv['vec'])


class CacheSecretLogic:
    _secret_cache_key = 'hs:{}:{}'
    _cache_dict = {}
    MAX_CACHE = 50

    def __init__(self, mongo, redis, secret, dt):
        self.mongo = mongo
        self.redis = redis
        if dt is None:
            dt = datetime.utcnow().date()
        self.date_ = dt
        self.date = str(dt)
        self.vector_logic = VectorLogic(self.mongo, dt=dt)
        self.secret = secret

    @property
    def secret_cache_key(self):
        return self._secret_cache_key.format(self.secret, self.date)

    def _get_secret_vector(self):
        return self.vector_logic.get_vector(self.secret)

    def _iterate_all_wv(self):
        return self.vector_logic.iterate_all()

    def set_secret(self, dry=False, force=False):
        if not force:
            if self.vector_logic.secret_logic.get_secret() is not None:
                raise ValueError("There is already a secret for this date")

            wv = self.mongo.find_one({'word': self.secret})
            if wv.get('secret_date') is not None:
                raise ValueError("This word was a secret in the past")

        secret_vec = self._get_secret_vector()

        nearest = []
        for word, vec in self._iterate_all_wv():
            s = self.vector_logic.calc_similarity(vec, secret_vec)
            heapq.heappush(nearest, (s, word))
            if len(nearest) > 1000:
                heapq.heappop(nearest)
        nearest.sort()
        self._cache_dict[self.date] = [w[1] for w in nearest]
        if not dry:
            self.do_populate()

    def do_populate(self):
        expiration = self.date_ - datetime.utcnow().date()  + timedelta(days=4)
        self.redis.rpush(self.secret_cache_key, *self.cache)
        self.redis.expire(self.secret_cache_key, expiration)
        self.vector_logic.secret_logic.set_secret(self.secret)

    @property
    def cache(self):
        cache = self._cache_dict.get(self.date)
        if cache is None or len(cache) < 1000:
                if len(self._cache_dict) > self.MAX_CACHE:
                    self._cache_dict.clear()
                self._cache_dict[self.date] = self.redis.lrange(self.secret_cache_key, 0, -1)
        return self._cache_dict[self.date]

    def get_cache_score(self, word):
        try:
            return self.cache.index(word) + 1
        except ValueError:
            return -1


class CacheSecretLogicGensim(CacheSecretLogic):
    def __init__(self, model_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import gensim.models.keyedvectors as word2vec
        self.model = word2vec.KeyedVectors.load(model_path).wv
        self.words = self.model.key_to_index.keys()

    def _get_secret_vector(self):
        return self.model[self.secret]

    def _iterate_all_wv(self):
        for word in self.words:
            yield word, self.model[word]
