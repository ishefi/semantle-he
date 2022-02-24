import multiprocessing

if __name__=="__main__":
    model_name = "model.mdl"
    model_input = "wiki.he.text"

    from gensim.models import Word2Vec
    from gensim.models.word2vec import LineSentence
    model = Word2Vec(LineSentence(model_input), sg=1, vector_size=100, window=5, min_count=20, workers=multiprocessing.cpu_count())
    model.init_sims(replace=True)
    model.save(model_name)