from argparse import ArgumentParser
from argparse import ArgumentTypeError
from datetime import datetime
import os
import random
import sys

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

from common.session import get_mongo
from common.session import get_redis
from logic import CacheSecretLogic
from logic import CacheSecretLogicGensim


def valid_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ArgumentTypeError("Bad date: should be of the format YYYY-mm-dd")


def main():
    parser = ArgumentParser("Set SematleHe secret for any date")
    parser.add_argument(
        '-s',
        '--secret',
        metavar='SECRET',
        help="Secret to set. If not provided, chooses a random word from Wikipedia.",
    )
    parser.add_argument(
        '-d', '--date', metavar='DATE', type=valid_date, help="Date of secret. If not provided today's date is used"
    )
    parser.add_argument(
        '--force', action='store_true', help="Allow rewriting dates or reusing secrets. Use with caution!"
    )
    parser.add_argument(
        '-m', '--model', help="Path to a gensim w2v model. If not provided, will use w2v data stored in mongodb."
    )

    args = parser.parse_args()

    mongo = get_mongo()
    redis = get_redis()

    if args.secret:
        secret = args.secret
    else:
        secret = get_random_word(mongo)
    do_populate(mongo, redis, args.model, secret, args.date, args.force)


def do_populate(mongo, redis, model, secret, date, force):
    if model:
        logic = CacheSecretLogicGensim(model, mongo, redis, secret, date)
    else:
        logic = CacheSecretLogic(mongo, redis, secret, date)
    logic.set_secret(dry=True, force=force)
    cache = logic.cache[::-1]
    print(cache)
    for rng in (range(i, i+10) for i in [1, 50, 100, 300, 550, 750]):
        for i in rng:
            w = cache[i]
            print(f"{i}: {w[::-1]}")
    pop = input("Populate?\n")
    if pop in ('y', 'Y'):
        logic.do_populate()
        print("Done!")
        exit(0)
    else:
        secret = get_random_word(mongo)
        do_populate(mongo, redis, model, secret, date, force)


def get_random_word(mongo):
    while True:
        secrets = mongo.aggregate([{'$sample': {'size': 100}}])
        for doc in secrets:
            secret = doc['word']
            if input(f'I chose {secret[::-1]}. Ok? [Ny] > ') in ('y', 'Y'):
                return secret


if __name__ == '__main__':
    main()
