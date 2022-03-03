#!/usr/bin/env python
from argparse import ArgumentError
from argparse import ArgumentParser
from pathlib import Path
from tqdm import tqdm

def main():
    parser = ArgumentParser("Post process HebPipe output to a single file")
    parser.add_argument("-f", "--folder", metavar="FOLDER", help="Input folder", required=True)
    parser.add_argument("-o", "--output", help='Output file', required=True)

    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        raise ArgumentError(None, message="--folder must be a valid folder")
    output = Path(args.output or args.folder)
    if output.exists():
        raise ArgumentError(None, message="--output must not be an existing file")

    files = list(folder.glob('**/*'))
    for fname in tqdm(files, desc='processing files', total=len(files), unit='file'):
        with output.open('ab+') as f2:
            with fname.open('rb') as f:
                lines = [clean_line(line.decode()) for line in f.readlines()]
            f2.write(' '.join(lines).strip().encode('utf-8'))



def clean_line(line):
    line = line.strip().replace("|", " ")
    if line in ("<s>", "</s>"):
        return '\n'
    else:
        return line


if __name__ == '__main__':
    try:
        main()
    except ArgumentError as e:
        print(e)
        exit(1)
