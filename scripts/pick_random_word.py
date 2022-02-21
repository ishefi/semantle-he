from argparse import ArgumentParser
import os
import random
import sys

import wikipedia
from wikipedia import WikipediaException

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

from common.session import get_session_factory
from logic import CacheSecretLogic


def main():
    parser = ArgumentParser("Pick random word and print some of its closest words")
    parser.add_argument(
        '-l', '--lite', help="Use SQLite local db", action="store_true"
    )
    args = parser.parse_args()

    redis = None  # no need for redis as this is "dry"
    session_factory = get_session_factory(args.lite)

    wikipedia.set_lang('he')
    while True:
        try:
            page = wikipedia.page(wikipedia.random(1)).content
        except WikipediaException:
            continue
        words = list(set(page.split()))
        secret = random.choice(words)
        if input(f'I chose {secret[::-1]}. Ok? [Ny] > ') in ('y', 'Y'):
            break

    csl = CacheSecretLogic(session_factory, redis, secret, None)
    csl.set_secret(dry=True)

    cache = csl.cache[::-1]
    for rng in (range(1, 11), range(100, 1000, 100)):
        for i in rng:
            score, w = cache[i]
            print(f"{i}: {score}: {w[::-1]}")


if __name__ == "__main__":
    main()
