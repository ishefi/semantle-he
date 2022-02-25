import multiprocessing
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence

from research.base import get_config

if __name__ == "__main__":
    config = get_config()
    MODEL_DUMP_PATH = config['MODEL_DUMP_PATH']
    MODEL_INPUT = config['MODEL_INPUT']

    model = Word2Vec(LineSentence(MODEL_INPUT), sg=1, vector_size=100, window=5, min_count=5,
                     workers=multiprocessing.cpu_count())
    model.save(MODEL_DUMP_PATH)
