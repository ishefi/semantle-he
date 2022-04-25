import glob
import json
import os
import sys
from pathlib import Path
import numpy as np

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

import gensim.models.keyedvectors as word2vec
from argparse import ArgumentParser

from common.session import get_mongo


class BasePopulater:
    def get_w2v(self):
        for word, vec, count in self._get_w2v():
            if self._is_all_he(word):
                yield word, vec, count

    def _is_all_he(self, word):
        return all(ord('א') <= ord(c) <= ord('ת') for c in word)


class GensimPopulater(BasePopulater):
    def __init__(self, inp):
        self.model = word2vec.KeyedVectors.load(inp).wv
        self.words = self.model.key_to_index.keys()

    def _get_w2v(self):
        for word in self.words:
            yield word, self.model[word].tobytes(), None


class JsonPopulater(BasePopulater):
    def __init__(self, inp):
        with open(inp) as f:
            self.w2vs = json.load(f)

    def _get_w2v(self):
        for word, vec, count in self.w2vs:
            yield word, np.array(vec).tobytes(), count


class ListsPopulater(BasePopulater):
    def __init__(self, folder):
        (vecs_file,) = glob.glob(f'{folder}/*.npy')
        (words_file,) = glob.glob(f'{folder}/*.txt')
        self.vecs = np.load(vecs_file).astype(np.float32)
        self.words = [w.strip() for w in open(words_file).readlines()]

    def _get_w2v(self):
        for word, vec in zip(self.words, self.vecs):
            yield word, vec.tobytes(), None


def main():
    parser = ArgumentParser("Populate vector table")
    parser.add_argument('-i', '--input', required=True, help='Input file (or folder for `lists`)')
    parser.add_argument(
        '-t', '--input-type', help='Type of input', choices=['gensim', 'json', 'lists'],
        default='gensim'
    )
    args = parser.parse_args()

    input = Path(args.input)
    if not input.is_absolute():
        input = Path(__file__).resolve().parent.parent / input

    if args.input_type == 'gensim':
        populator = GensimPopulater(input)
    elif args.input_type == 'json':
        populator = JsonPopulater(input)
    else:
        populator = ListsPopulater(input)

    mongo = get_mongo()
    to_insert = []
    for i, w2v in enumerate(populator.get_w2v()):
        word, vec, count = w2v
        doc = {'word': word, 'vec': vec}
        if count is not None:
            doc['count'] = count
        to_insert.append(doc)
        if i % 5000 == 0:
            print(f"Done {i}/{len(populator.words)}")
            mongo.insert_many(to_insert)
            to_insert = []
    if to_insert:
        mongo.insert_many(to_insert)


if __name__ == "__main__":
    main()
