from __future__ import annotations
import struct
from typing import TYPE_CHECKING

from gensim.models import KeyedVectors
from numpy import dot
from numpy.linalg.linalg import norm
import numpy as np

from common.consts import VEC_SIZE

if TYPE_CHECKING:
    from typing import AsyncIterator
    from common.typing import np_float_arr

class GensimModel:

    def __init__(self, model: KeyedVectors):
        self.model = model

    async def get_vector(self, word: str) -> np_float_arr | None:
        if not all(ord('א') <= ord(c) <= ord('ת') for c in word):
            return None
        if len(word) == 1:
            return None
        if word not in self.model:
            return None
        vector: np_float_arr = self.model[word].tolist()
        return vector

    async def get_similarities(self, words: list[str], vector: np_float_arr) -> np_float_arr:
        similarities: np_float_arr = np.round(
            self.model.cosine_similarities(
                vector, np.asarray([self.model[w] for w in words])) * 100, 2
        )
        return similarities

    async def iterate_all(self) -> AsyncIterator[tuple[str, np_float_arr]]:
        for word in self.model.key_to_index.keys():
            if isinstance(word, str):
                vector = await self.get_vector(word)
            else:
                continue
            if vector is None:
                continue
            yield word, self.model[word]

    async def calc_similarity(self, vec1: np_float_arr, vec2: np_float_arr) -> float:
        similarities: np_float_arr = self.model.cosine_similarities(
            vec1, np.expand_dims(vec2, axis=0)
        )
        return round(float(similarities[0]) * 100 , 2)
