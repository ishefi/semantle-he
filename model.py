import struct
from abc import ABC, abstractmethod

from gensim.models import KeyedVectors
from numpy import dot
from numpy.linalg.linalg import norm
import numpy as np

from common.consts import VEC_SIZE


class Model(ABC):

    @abstractmethod
    async def get_vector(self, word: str):
        pass

    @abstractmethod
    async def get_similarities(self, words: [str], vector: [float]) -> [float]:
        pass

    @abstractmethod
    async def iterate_all(self):
        pass

    @abstractmethod
    async def calc_similarity(self, vec1: [float], vec2: [float]):
        pass


class GensimModel(Model):

    def __init__(self, model: KeyedVectors):
        self.model = model

    async def get_vector(self, word: str):
        if word not in self.model:
            return
        return self.model[word].tolist()

    async def get_similarities(self, words: [str], vector: [float]) -> [float]:
        return np.round(self.model.cosine_similarities(vector, np.asarray([self.model[w] for w in words])) * 100, 2)

    async def iterate_all(self):
        for word in self.model:
            yield word, self.model[word]

    async def calc_similarity(self, vec1: [float], vec2: [float]) -> float:
        return round(self.model.cosine_similarities(vec1, np.expand_dims(vec2, axis=0))[0] * 100 , 2)


class MongoModel(Model):
    _secret_cache = {}

    def __init__(self, mongo):
        self.mongo = mongo

    async def get_vector(self, word: str):
        w2v = await self.mongo.find_one({'word': word})
        if w2v is None:
            return None
        else:
            return self._unpack_vector(w2v['vec'])

    def _unpack_vector(self, raw_vec):
        return struct.unpack(VEC_SIZE, raw_vec)

    async def get_similarities(self, words: [str], vector: [float]) -> [float]:
        wvs = self.mongo.find({'word': {'$in': words}})
        return {
            wv['word']: await self.calc_similarity(vector, self._unpack_vector(wv['vec']))
            for wv in await wvs.to_list(None)
        }

    async def calc_similarity(self, vec1: [float], vec2: [float]):
        return round(dot(vec1, vec2) / (norm(vec1) * norm(vec2)) * 100, 2)

    async def iterate_all(self):
        for wv in await self.mongo.find().to_list(None):
            yield wv['word'], self._unpack_vector(wv['vec'])
