import json

from gensim.models import Word2Vec
import numpy as np

CUTOFF_RANK = 50000
MODEL_PATH = "model.mdl"
VECTORS_PATH = "model.mdl.wv.vectors.npy"
DUMP_PATH = 'vectors.json'

if __name__ == "__main__":
    model = Word2Vec.load(MODEL_PATH)
    sorted_indices = np.argsort(-model.wv.expandos['count'])
    top_indices = sorted_indices[:CUTOFF_RANK]
    vectors = np.load(VECTORS_PATH)
    top_vectors = vectors[top_indices]
    top_words = [model.wv.index_to_key[i] for i in top_indices]

    with open(DUMP_PATH, 'w', encoding='utf-8') as f:
        json.dump([{'word': w, 'vec': v.tolist()} for w, v in zip(top_words, top_vectors)], f, ensure_ascii=False)

    print(top_words[:10])
