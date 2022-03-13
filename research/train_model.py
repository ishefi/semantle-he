import logging
import multiprocessing
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence

from research.base import get_config, get_absolute_path

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
    model.save(str(MODEL_DUMP_PATH))

    print(f'loss is {model.get_latest_training_loss()}')