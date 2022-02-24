from pathlib import Path

from gensim.corpora import WikiCorpus
from gensim.test.utils import datapath
import urllib3
import pathlib

from research.config import WIKIFILE, CORPUS_OUTPUT


def download(url: str, dump_path: Path):
    if dump_path.exists():
        print("skipping download. file exists")
        return
    chunk_size = 1024
    http = urllib3.PoolManager(cert_reqs='CERT_NONE')
    r = http.request('GET', url, preload_content=False)
    with dump_path.open('wb') as out:
        data = r.read(chunk_size)
        while data:
            out.write(data)
            data = r.read(chunk_size)
    r.release_conn()


if __name__ == "__main__":
    url = f"https://dumps.wikimedia.org/hewiki/latest/{WIKIFILE}"
    bz_temp_dump_path = pathlib.Path(__file__).parent.resolve() / Path(WIKIFILE)
    download(url, bz_temp_dump_path)

    wiki = WikiCorpus(datapath(str(bz_temp_dump_path)), dictionary={})

    corpus_output = Path(CORPUS_OUTPUT)
    print("Starting to create wiki corpus")
    with corpus_output.open('wb') as output:
        for i, text in enumerate(wiki.get_texts(), start=1):
            article = " ".join(text)
            output.write(f"{article}\n".encode('utf-8'))
            if i % 1000 == 0:
                print(f"Saved {i} articles")

    print(f"Finished - Saved {i} articles")
