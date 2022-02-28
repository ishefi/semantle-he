from argparse import ArgumentParser
from argparse import ArgumentTypeError
from datetime import datetime
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
    parser.add_argument('secret', metavar='SECRET', help="Secret to set")
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

    if args.model:
        logic = CacheSecretLogicGensim(args.model, mongo, redis, args.secret, args.date)
    else:
        logic = CacheSecretLogic(mongo, redis, args.secret, args.date)
    logic.set_secret(dry=True, force=args.force)
    cache = logic.cache[::-1]
    print(cache)
    for rng in (range(i, i+10) for i in [1, 50, 100, 300, 550, 750]):
        for i in rng:
            w = cache[i]
            print(f"{i}: {w[::-1]}")
    pop = input("Populate?\n")
    if pop in ('y', 'Y'):
        logic.do_populate()


if __name__ == '__main__':
    main()
