import multiprocessing
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence

MODEL_DUMP_PATH = "model.mdl"
MODEL_INPUT = "wiki.he.text"

if __name__ == "__main__":
    model = Word2Vec(LineSentence(MODEL_INPUT), sg=1, vector_size=100, window=5, min_count=5,
                     workers=multiprocessing.cpu_count())
    model.init_sims(replace=True)
    model.save(MODEL_DUMP_PATH)
