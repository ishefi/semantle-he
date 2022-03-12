from argparse import ArgumentParser
from argparse import ArgumentTypeError
from datetime import datetime
from datetime import timedelta
import os
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
    parser.add_argument(
        '-i', '--iterative', action='store_true', help="If provided, run in an iterative mode, starting the given date"
    )

    args = parser.parse_args()

    mongo = get_mongo()
    redis = get_redis()

    if args.secret:
        secret = args.secret
    else:
        secret = get_random_word(mongo)
    date = args.date
    do_populate(mongo, redis, args.model, secret, date, args.force)
    if args.iterative:
        date += timedelta(days=1)
        print(f"Now doing {date}")
        do_populate(mongo, redis, args.model, get_random_word(mongo), date, args.force)


def do_populate(mongo, redis, model, secret, date, force):
    if model:
        logic = CacheSecretLogicGensim(model, mongo, redis, secret, date)
    else:
        logic = CacheSecretLogic(mongo, redis, secret, date)
    logic.set_secret(dry=True, force=force)
    cache = [w[::-1] for w in logic.cache[::-1]]
    print(cache[0])
    for rng in (range(i, i+10) for i in [1, 50, 100, 300, 550, 750]):
        for i in rng:
            w = cache[i]
            print(f"{i}: {w[::-1]}")
    pop = input("Populate?\n")
    if pop in ('y', 'Y'):
        logic.do_populate()
        print("Done!")
        return True
    else:
        secret = get_random_word(mongo)
        return do_populate(mongo, redis, model, secret, date, force)


def get_random_word(mongo):
    while True:
        secrets = mongo.aggregate([{'$sample': {'size': 100}}])
        for doc in secrets:
            secret = doc['word']
            if best_secret := get_best_secret(secret):
                return best_secret


def get_best_secret(secret):
    inp = input(f'I chose {secret[::-1]}. Ok? [Ny] > ')
    if inp in 'nN':
        return ''
    if inp in ('y', 'Y'):
        return secret
    else:
        return get_best_secret(inp)


if __name__ == '__main__':
    main()
