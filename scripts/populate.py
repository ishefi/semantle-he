from __future__ import annotations
import glob
import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

import numpy as np

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

import gensim.models.keyedvectors as word2vec
from argparse import ArgumentParser

from common.session import get_mongo


if TYPE_CHECKING:
    from typing import Iterable


class BasePopulater(ABC):
    def get_w2v(self) -> Iterable[tuple[str, bytes, int | None]]:
        for word, vec, count in self._get_w2v():
            if self._is_all_he(word):
                yield word, vec, count

    @abstractmethod
    def _get_w2v(self) -> Iterable[tuple[str, bytes, int | None]]:
        pass

    def _is_all_he(self, word: str) -> bool:
        return all(ord('א') <= ord(c) <= ord('ת') for c in word)


class GensimPopulater(BasePopulater):
    def __init__(self, inp: str):
        self.model = word2vec.KeyedVectors.load(inp).wv
        self.words = self.model.key_to_index.keys()

    def _get_w2v(self) -> Iterable[tuple[str, bytes, int | None]]:
        for word in self.words:
            yield word, self.model[word].tobytes(), None


class JsonPopulater(BasePopulater):
    def __init__(self, inp: str):
        with open(inp) as f:
            self.w2vs = json.load(f)

    def _get_w2v(self) -> Iterable[tuple[str, bytes, int | None]]:
        for word, vec, count in self.w2vs:
            yield word, np.array(vec).tobytes(), count


class ListsPopulater(BasePopulater):
    def __init__(self, folder: str):
        (vecs_file,) = glob.glob(f'{folder}/*.npy')
        (words_file,) = glob.glob(f'{folder}/*.txt')
        self.vecs = np.load(vecs_file).astype(np.float32)
        self.words = [w.strip() for w in open(words_file).readlines()]

    def _get_w2v(self) -> Iterable[tuple[str, bytes, int | None]]:
        for word, vec in zip(self.words, self.vecs):
            yield word, vec.tobytes(), None


def main() -> None:
    parser = ArgumentParser("Populate vector table")
    parser.add_argument('-i', '--input', required=True, help='Input file (or folder for `lists`)')
    parser.add_argument(
        '-t', '--input-type', help='Type of input', choices=['gensim', 'json', 'lists'],
        default='gensim'
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = Path(__file__).resolve().parent.parent / input_path
    input_path_str = str(input_path)
    populator: BasePopulater
    if args.input_type == 'gensim':
        populator = GensimPopulater(input_path_str)
    elif args.input_type == 'json':
        populator = JsonPopulater(input_path_str)
    else:
        populator = ListsPopulater(input_path_str)

    mongo = get_mongo()
    to_insert = []
    for i, w2v in enumerate(populator.get_w2v()):
        word, vec, count = w2v
        doc: dict[str, str | bytes | int] = {'word': word, 'vec': vec}
        if count is not None:
            doc['count'] = count
        to_insert.append(doc)
        if i % 5000 == 0:
            if hasattr(populator, 'words'):
                print(f"Done {i}/{len(populator.words)}")
            mongo.insert_many(to_insert)
            to_insert = []
    if to_insert:
        mongo.insert_many(to_insert)


if __name__ == "__main__":
    main()
