from argparse import ArgumentParser
import os
import random
import sys

import wikipedia
from wikipedia import WikipediaException

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

from common.session import get_mongo
from logic import CacheSecretLogic


def main():
    redis = None  # no need for redis as this is "dry"
    mongo = get_mongo()
    wikipedia.set_lang('he')
    secret = ''
    while True:
        try:
            page = wikipedia.page(wikipedia.random(1)).content
        except WikipediaException:
            continue
        words = list(set(page.split()))
        secret = random.choice(words)
        if input(f'I chose {secret[::-1]}. Ok? [Ny] > ') in ('y', 'Y'):
            break

    csl = CacheSecretLogic(mongo, redis, secret, None)
    csl.set_secret(dry=True)

    cache = csl.cache[::-1]
    for rng in (range(1, 11), range(100, 1000, 100)):
        for i in rng:
            score, w = cache[i]
            print(f"{i}: {score}: {w[::-1]}")


if __name__ == "__main__":
    main()
