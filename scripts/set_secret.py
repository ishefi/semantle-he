from argparse import ArgumentParser
from argparse import ArgumentTypeError
from datetime import datetime
import os
import sys

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

from common.session import get_redis
from common.session import get_session_factory
from logic import CacheSecretLogic


def valid_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ArgumentTypeError("Bad date: should be of the format YYYY-mm-dd")


def main():
    parser = ArgumentParser("Set SematleHe secret for any date")
    parser.add_argument('secret', metavar='SECRET', help="Secret to set")
    parser.add_argument(
        '-d', '--date', metavar='DATE', type=valid_date, help="Date of secret. If not provided today's date is used"
    )
    parser.add_argument(
        '-l', '--lite', help="Use SQLite", action="store_true"
    )

    args = parser.parse_args()

    session_factory = get_session_factory(args.lite)
    redis = get_redis()

    logic = CacheSecretLogic(session_factory, redis, args.secret, args.date)
    logic.set_secret()


if __name__ == '__main__':
    main()
