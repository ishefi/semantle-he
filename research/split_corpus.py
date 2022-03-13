from pathlib import Path
from typing import List

from tqdm import tqdm

from research.base import get_config, get_absolute_path


def get_num_articles(corpus_output: Path):
    with corpus_output.open('rb') as f:
        num_articles = sum(1 for _ in f.readlines())
    return num_articles


def write_single_split(lines: List[bytes], split_corpus_output_folder: Path, corpus_output: Path, curr_split: int,
                       num_digits: int):
    path = split_corpus_output_folder / Path(corpus_output.stem + str(curr_split).zfill(num_digits) + ".txt")
    with path.open('wb') as output:
        for line in lines:
            output.write(f"{line.decode('utf-8')}\n".encode('utf-8'))


def split(corpus_path: Path, split_corpus_output_folder: Path, split_every: int):
    num_articles = get_num_articles(corpus_path)
    num_digits = len(str(num_articles // SPLIT_EVERY))
    curr_split = 1
    lines = []
    with corpus_path.open('rb') as f:
        for i, article in tqdm(enumerate(f.readlines(), start=1), desc="splitting corpus to articles",
                               total=num_articles):
            lines.append(article)
            if i % split_every == 0:
                write_single_split(lines, split_corpus_output_folder, corpus_path, curr_split, num_digits)
                lines = []
                curr_split += 1
    if lines:
        write_single_split(lines, split_corpus_output_folder, corpus_path, curr_split, num_digits)
    print(f"Finished - Saved {i}/{num_articles} articles")


if __name__ == "__main__":
    config = get_config()
    CORPUS_OUTPUT = config['CORPUS_OUTPUT']
    SPLIT_EVERY = config['SPLIT_CORPUS_EVERY']
    SPLIT_CORPUS_OUTPUT_FOLDER = config["SPLIT_CORPUS_OUTPUT_FOLDER"]

    corpus_output_folder = get_absolute_path(SPLIT_CORPUS_OUTPUT_FOLDER)
    corpus_path = get_absolute_path(CORPUS_OUTPUT)
    split(corpus_path, corpus_output_folder, SPLIT_EVERY)
