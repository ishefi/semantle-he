import struct

from gensim.models import KeyedVectors
from numpy import dot
from numpy.linalg.linalg import norm
import numpy as np

from common.consts import VEC_SIZE


class GensimModel:

    def __init__(self, model: KeyedVectors):
        self.model = model

    async def get_vector(self, word: str):
        if not all(ord('א') <= ord(c) <= ord('ת') for c in word):
            return
        if len(word) == 1:
            return
        if word not in self.model:
            return
        return self.model[word].tolist()

    async def get_similarities(self, words: [str], vector: [float]) -> [float]:
        return np.round(self.model.cosine_similarities(vector, np.asarray([self.model[w] for w in words])) * 100, 2)

    async def iterate_all(self):
        for word in self.model.key_to_index.keys():
            vector = await self.get_vector(word)
            if vector is None:
                continue
            yield word, self.model[word]

    async def calc_similarity(self, vec1: [float], vec2: [float]) -> float:
        return round(self.model.cosine_similarities(vec1, np.expand_dims(vec2, axis=0))[0] * 100 , 2)
