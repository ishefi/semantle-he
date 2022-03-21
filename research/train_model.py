import logging
import multiprocessing
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence
import numpy as np

from research.base import get_config, get_absolute_path

def remove_non_hebrew_words(model):
    wv = model.wv
    ids_to_trim = []
    for i, word in enumerate(wv.index_to_key):
        if (not all(ord('א') <= ord(c) <= ord('ת') for c in word)) or len(word) ==1:
            ids_to_trim.append(i)

    wv.vectors = np.delete(wv.vectors, ids_to_trim, axis=0)
    wv.expandos['count'] = np.delete(wv.expandos['count'], ids_to_trim, axis=0)
    wv.init_sims(replace=True)

    for i in sorted(ids_to_trim, reverse=True):
        del wv.index_to_key[i]

if __name__ == "__main__":
    config = get_config()
    SEED = 42
    MODEL_DUMP_PATH = get_absolute_path(config['MODEL_DUMP_PATH'])
    MODEL_INPUT = get_absolute_path(config['MODEL_INPUT'])
    print(f'reading from {MODEL_INPUT}')
    print(f'dumping to {MODEL_DUMP_PATH}')

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    model = Word2Vec(LineSentence(str(MODEL_INPUT)), sg=1, vector_size=100, window=5, min_count=5,
                     workers=multiprocessing.cpu_count(), compute_loss=True, seed=SEED)

    print('removing non hebrew words from model')
    remove_non_hebrew_words(model)
    print(f'saving model with {len(model.wv.index_to_key)} vectors')
    model.save(str(MODEL_DUMP_PATH))

    print(f'loss is {model.get_latest_training_loss()}')

