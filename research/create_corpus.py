import os.path

from gensim.corpora import WikiCorpus
from gensim.test.utils import datapath
import urllib3


def download():
    url = "https://dumps.wikimedia.org/hewiki/latest/hewiki-latest-pages-articles.xml.bz2"
    path = 'hewiki-latest-pages-articles.xml.bz2'

    if os.path.exists(path):
        print("skipping download")
        return
    chunk_size = 1024
    http = urllib3.PoolManager(cert_reqs='CERT_NONE')
    r = http.request('GET', url, preload_content=False)
    with open(path, 'wb') as out:
        while True:
            data = r.read(chunk_size)
            if not data:
                break
            out.write(data)
    r.release_conn()


if __name__ == "__main__":
    download()
    inp = datapath(r'C:\Users\Iddo\Documents\semantle-he\research\hewiki-latest-pages-articles.xml.bz2')
    outp = "wiki.he.text"
    print("Starting to create wiki corpus")

    space = " "
    wiki = WikiCorpus(inp, dictionary={})
    with open(outp, 'wb') as output:
        for i, text in enumerate(wiki.get_texts(), start=1):
            article = " ".join(text)
            output.write("{}\n".format(article).encode('utf-8'))
            if (i % 1000 == 0):
                print(f"Saved {i} articles")

    print(f"Finished - Saved {i} articles")
