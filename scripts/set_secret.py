from argparse import ArgumentParser
from argparse import ArgumentTypeError
import asyncio
from datetime import datetime
from datetime import timedelta
import os
import sys


base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

from common import config
from common.session import get_mongo, get_model
from common.session import get_redis
from logic import CacheSecretLogic
from logic import CacheSecretLogicGensim


def valid_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise ArgumentTypeError("Bad date: should be of the format YYYY-mm-dd")


async def main():
    parser = ArgumentParser("Set SematleHe secret for any date")
    parser.add_argument(
        '-s',
        '--secret',
        metavar='SECRET',
        help="Secret to set. If not provided, chooses a random word from Wikipedia.",
    )
    parser.add_argument(
        '-d', '--date', metavar='DATE', type=valid_date,
        help="Date of secret. If not provided, first date w/o secret is used"
    )
    parser.add_argument(
        '--force', action='store_true', help="Allow rewriting dates or reusing secrets. Use with caution!"
    )
    parser.add_argument(
        '-m', '--model_path', help="Path to a gensim w2v model. If not provided, will use w2v data stored in mongodb."
    )
    parser.add_argument(
        '-i', '--iterative', action='store_true', help="If provided, run in an iterative mode, starting the given date"
    )

    args = parser.parse_args()

    mongo = get_mongo()
    redis = get_redis()
    has_model = hasattr(config, "model_zip_id")
    model = get_model(has_model=has_model, mongo=mongo)

    if args.date:
        date = args.date
    else:
        date = await get_date(mongo)
    if args.secret:
        secret = args.secret
    else:
        secret = await get_random_word(mongo)
    while True:
        await do_populate(mongo, redis, has_model, secret, date, model, args.force)
        if not args.iterative:
            break
        date += timedelta(days=1)
        print(f"Now doing {date}")
        secret = await get_random_word(mongo)


async def get_date(mongo):
    cursor = mongo.find({"secret_date": {"$exists": 1}})
    cursor = cursor.sort("secret_date", -1)
    latest = await cursor.next()
    date_str = latest["secret_date"]
    dt = valid_date(date_str) + timedelta(days=1)
    print(f"Now doing {dt}")
    return dt


async def do_populate(mongo, redis, has_model, secret, date, model, force):
    if has_model:
        logic = CacheSecretLogicGensim('model.mdl', mongo, redis, secret, dt=date, model=model)
    else:
        logic = CacheSecretLogic(mongo, redis, secret, dt=date, model=model)
    await logic.set_secret(dry=True, force=force)
    cache = [w[::-1] for w in (await logic.cache)[::-1]]
    print(' ,'.join(cache))
    print(cache[0])
    for rng in (range(i, i + 10) for i in [1, 50, 100, 300, 550, 750]):
        for i in rng:
            w = cache[i]
            print(f"{i}: {w}")
    pop = input("Populate?\n")
    if pop in ('y', 'Y'):
        await logic.do_populate()
        print("Done!")
        return True
    else:
        secret = await get_random_word(mongo)
        return await do_populate(mongo, redis, has_model, secret, date, model, force)


async def get_random_word(mongo):
    while True:
        secrets = mongo.aggregate([{'$sample': {'size': 100}}])
        async for doc in secrets:
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
    asyncio.run(main())
