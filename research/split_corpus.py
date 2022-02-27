from pathlib import Path

from tqdm import tqdm

from research.base import get_config

if __name__ == "__main__":
    config = get_config()
    CORPUS_OUTPUT = config['CORPUS_OUTPUT']
    SPLIT_EVERY = config['SPLIT_CORPUS_EVERY']
    SPLIT_CORPUS_OUTPUT_FOLDER = config["SPLIT_CORPUS_OUTPUT_FOLDER"]

    base_folder = Path(__file__).parent.resolve()
    corpus_output_folder = base_folder / Path(SPLIT_CORPUS_OUTPUT_FOLDER)
    corpus_output = base_folder / Path(CORPUS_OUTPUT)
    print("Starting to split wiki corpus")

    with corpus_output.open('rb') as f:
        num_articles = sum(1 for _ in f.readlines())

    num_digits = len(str(num_articles // SPLIT_EVERY))
    split = 1
    lines = []
    with corpus_output.open('rb') as f:
        for i, article in tqdm(enumerate(f.readlines(), start=1), desc="splitting corpus to articles",
                               total=num_articles):
            lines.append(article)
            if i % SPLIT_EVERY == 0:
                path = SPLIT_CORPUS_OUTPUT_FOLDER / Path(corpus_output.stem + str(split).zfill(num_digits) + ".txt")
                with path.open('wb') as output:
                    for line in lines:
                        output.write(f"{line.decode('utf-8')}\n".encode('utf-8'))
                lines = []
                split += 1
    if lines:
        path = SPLIT_CORPUS_OUTPUT_FOLDER / Path(corpus_output.stem + str(split).zfill(num_digits) + ".txt")
        with path.open('wb') as output:
            for article in lines:
                output.write(f"{article}\n".encode('utf-8'))

    print(f"Finished - Saved {i}/{num_articles} articles")
