import os
import sqlite3
import sys

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

import gensim.models.keyedvectors as word2vec
from argparse import ArgumentParser

from common.session import get_session_factory
from common.tables import Word2Vec


def main():
    parser = ArgumentParser("Populate vector table")
    parser.add_argument('-i', '--input', required=True, help='Input file')
    parser.add_argument('-l', '--lite', help="Use sqlite", action='store_true')
    args = parser.parse_args()

    model = word2vec.KeyedVectors.load(args.input).wv
    words = model.key_to_index.keys()
    if args.lite:
        do_sqlite(model, words)
    else:
        do_remote_sql(model, words)


def do_sqlite(model, words):
    con = sqlite3.connect('word2vec.db')
    cur = con.cursor()
    cur.execute("""create table if not exists word2vec (word text, vec blob)""")
    con.commit()
    cur.execute("""create unique index if not exists word2vec_word on word2vec (word)""")
    con.commit()
    for i, word in enumerate(words):
        if i % 1111 == 0:
            con.commit()
        vec = model[word].tobytes()
        cur.execute("insert into word2vec values(?,?)", (word, vec))
    con.commit()


def do_remote_sql(model, words):
    session_factory = get_session_factory()
    session = session_factory()
    session.begin()
    prev_words = list(w.word for w in session.query(Word2Vec.word))
    for i, word in enumerate(words):
        if i % 1000 == 0:
            print(f"Done {i}/{len(words)}")
        if word in prev_words or i == 22163:
            continue
        vec = model[word].tobytes()

        session.add(Word2Vec(word=word, vec=vec))
        # if True:
        if i % 1000 == 0:
            try:
                session.commit()
                session.begin()
            except:
                print(f"I IS: {i}")
                raise

    session.commit()


if __name__ == "__main__":
    main()
