import os
import sys

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

import gensim.models.keyedvectors as word2vec
from argparse import ArgumentParser

from common.session import get_mongo


def main():
    parser = ArgumentParser("Populate vector table")
    parser.add_argument('-i', '--input', required=True, help='Input file')
    args = parser.parse_args()

    model = word2vec.KeyedVectors.load(args.input).wv
    words = model.key_to_index.keys()
    mongo = get_mongo()
    collection = mongo
    to_insert = []
    for i, word in enumerate(words):
        vec = model[word].tobytes()
        to_insert.append({'word': word, 'vec': vec})
        if i % 5000 == 0:
            print(f"Done {i}/{len(words)}")
            collection.insert_many(to_insert)
            to_insert = []
    if to_insert:
        collection.insert_many(to_insert)

if __name__ == "__main__":
    main()
