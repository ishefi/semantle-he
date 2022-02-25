import json
from gensim.models import Word2Vec

from research.base import get_config

if __name__ == "__main__":
    config = get_config()
    MODEL_PATH = config['MODEL_PATH']
    VECTORS_PATH = config['VECTORS_PATH']
    DUMP_PATH = config['DUMP_PATH']

    model = Word2Vec.load(MODEL_PATH)
    counts = model.wv.expandos['count']
    vectors = model.wv.vectors
    top_words = [model.wv.index_to_key[i] for i in range(len(counts))]

    with open(DUMP_PATH, 'w', encoding='utf-8') as f:
        json.dump([{'word': w, 'vec': v.tolist(), 'count': c} for w, v, c in zip(top_words, vectors, counts)], f,
                  ensure_ascii=False)

    print(top_words[:10])
