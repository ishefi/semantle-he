from pathlib import Path

from gensim.corpora import WikiCorpus
from gensim.test.utils import datapath
import urllib3
from tqdm import tqdm

from research.base import get_config, get_absolute_path


def download_corpus(url: str, dump_path: Path):
    if dump_path.exists():
        print("skipping download. file exists")
        return
    chunk_size = 1024
    http = urllib3.PoolManager(cert_reqs='CERT_NONE')
    r = http.request('GET', url, preload_content=False)

    i = 0
    with dump_path.open('wb') as out:
        pbar = tqdm(total=int(r.headers['Content-Length']), unit='B', unit_scale=True, desc='Downloading corpus')
        data = r.read(chunk_size)
        while data:
            i += 1
            out.write(data)
            pbar.update(len(data))
            data = r.read(chunk_size)
    pbar.close()
    r.release_conn()


def corpus_to_text(corpus_output: Path, dump_path: Path):
    wiki = WikiCorpus(datapath(str(dump_path)), dictionary={})
    print("Starting to create wiki corpus")
    with corpus_output.open('wb') as output:
        for i, text in tqdm(enumerate(wiki.get_texts(), start=1), desc="saving articles", unit='articles',
                            mininterval=5):
            article = " ".join(text)
            output.write(f"{article}\n".encode('utf-8'))


if __name__ == "__main__":
    config = get_config()
    WIKIFILE = config['WIKIFILE']
    CORPUS_OUTPUT = config['CORPUS_OUTPUT']
    dump_path = get_absolute_path(WIKIFILE)
    corpus_output = get_absolute_path(config['CORPUS_OUTPUT'])

    download_corpus(url=f"https://dumps.wikimedia.org/hewiki/latest/{WIKIFILE}", dump_path=dump_path)
    corpus_to_text(corpus_output, dump_path)
