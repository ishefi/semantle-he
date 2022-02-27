from pathlib import Path

from gensim.corpora import WikiCorpus
from gensim.test.utils import datapath
import urllib3
import pathlib
from tqdm import tqdm

from research.base import get_config


def download(url: str, dump_path: Path):
    if dump_path.exists():
        print("skipping download. file exists")
        return
    chunk_size = 1024
    http = urllib3.PoolManager(cert_reqs='CERT_NONE')
    r = http.request('GET', url, preload_content=False)

    i=0
    with dump_path.open('wb') as out:
        pbar = tqdm(total=int(r.headers['Content-Length']), unit='B', unit_scale=True, desc='Downloading corpus')
        data = r.read(chunk_size)
        while data:
            i+=1
            out.write(data)
            pbar.update(len(data))
            data = r.read(chunk_size)
    pbar.close()
    r.release_conn()


if __name__ == "__main__":
    config = get_config()
    WIKIFILE = config['WIKIFILE']
    CORPUS_OUTPUT = config['CORPUS_OUTPUT']
    url = f"https://dumps.wikimedia.org/hewiki/latest/{WIKIFILE}"
    bz_temp_dump_path = pathlib.Path(__file__).parent.resolve() / Path(WIKIFILE)
    download(url, bz_temp_dump_path)

    wiki = WikiCorpus(datapath(str(bz_temp_dump_path)), dictionary={})
    corpus_output = Path(CORPUS_OUTPUT)
    print("Starting to create wiki corpus")
    pbar = tqdm(desc="saving articles", unit='articles')
    with corpus_output.open('wb') as output:
        for i, text in enumerate(wiki.get_texts(), start=1):
            article = " ".join(text)
            output.write(f"{article}\n".encode('utf-8'))
            if i % 1000 == 0:
                pbar.update(i)
