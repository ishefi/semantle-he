import json
from gensim.models import Word2Vec
import numpy as np

from research.base import get_config

if __name__ == "__main__":
    config = get_config()
    CUTOFF_RANK = config['CUTOFF_RANK']
    MODEL_PATH = config['MODEL_PATH']
    VECTORS_PATH = config['VECTORS_PATH']
    DUMP_PATH = config['DUMP_PATH']

    model = Word2Vec.load(MODEL_PATH)
    sorted_indices = np.argsort(-model.wv.expandos['count'])
    top_indices = sorted_indices[:CUTOFF_RANK]
    vectors = np.load(VECTORS_PATH)
    top_vectors = vectors[top_indices]
    top_words = [model.wv.index_to_key[i] for i in top_indices]

    with open(DUMP_PATH, 'w', encoding='utf-8') as f:
        json.dump([{'word': w, 'vec': v.tolist()} for w, v in zip(top_words, top_vectors)], f, ensure_ascii=False)

    print(top_words[:10])
