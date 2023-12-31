#!/usr/bin/env python
from __future__ import annotations

import asyncio
import datetime
import os
import sys
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from typing import TYPE_CHECKING

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

from common.session import get_model  # noqa: E402
from common.session import get_mongo  # noqa: E402
from common.session import get_redis  # noqa: E402
from logic.game_logic import CacheSecretLogic  # noqa: E402

if TYPE_CHECKING:
    from typing import Any

    from motor.core import AgnosticCollection
    from redis.asyncio import Redis

    from model import GensimModel


def valid_date(date_str: str) -> datetime.date:
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ArgumentTypeError("Bad date: should be of the format YYYY-mm-dd")


async def main() -> None:
    parser = ArgumentParser("Set SematleHe secret for any date")
    parser.add_argument(
        "-s",
        "--secret",
        metavar="SECRET",
        help="Secret to set. If not provided, chooses a random word from Wikipedia.",
    )
    parser.add_argument(
        "-d",
        "--date",
        metavar="DATE",
        type=valid_date,
        help="Date of secret. If not provided, first date w/o secret is used",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow rewriting dates or reusing secrets. Use with caution!",
    )
    parser.add_argument(
        "-m",
        "--model_path",
        help="Path to a gensim w2v model. If not provided, will use w2v data stored in mongodb.",
    )
    parser.add_argument(
        "-i",
        "--iterative",
        action="store_true",
        help="If provided, run in an iterative mode, starting the given date",
    )

    args = parser.parse_args()

    mongo = get_mongo().word2vec2
    redis = get_redis()
    model = get_model()

    if args.date:
        date = args.date
    else:
        date = await get_date(mongo)
    if args.secret:
        secret = args.secret
    else:
        secret = await get_random_word(mongo)
    while True:
        await do_populate(mongo, redis, secret, date, model, args.force)
        if not args.iterative:
            break
        date += datetime.timedelta(days=1)
        print(f"Now doing {date}")
        secret = await get_random_word(mongo)


async def get_date(word2vec: AgnosticCollection[Any]) -> datetime.date:
    cursor = word2vec.find({"secret_date": {"$exists": 1}})
    cursor = cursor.sort("secret_date", -1)
    latest: dict[str, Any] = await cursor.next()
    date_str = latest["secret_date"]
    dt = valid_date(date_str) + datetime.timedelta(days=1)
    print(f"Now doing {dt}")
    return dt


async def do_populate(
    mongo: AgnosticCollection[Any],
    redis: Redis[Any],
    secret: str,
    date: datetime.date,
    model: GensimModel,
    force: bool,
) -> bool:
    logic = CacheSecretLogic(mongo, redis, secret, dt=date, model=model)
    await logic.set_secret(dry=True, force=force)
    cache = [w[::-1] for w in (await logic.cache)[::-1]]
    print(" ,".join(cache))
    print(cache[0])
    for rng in (range(i, i + 10) for i in [1, 50, 100, 300, 550, 750]):
        for i in rng:
            w = cache[i]
            print(f"{i}: {w}")
    pop = input("Populate?\n")
    if pop in ("y", "Y"):
        await logic.do_populate()
        print("Done!")
        return True
    else:
        secret = await get_random_word(mongo)
        return await do_populate(mongo, redis, secret, date, model, force)


async def get_random_word(word2vec: AgnosticCollection[Any]) -> str:
    while True:
        secrets = word2vec.aggregate([{"$sample": {"size": 100}}])
        async for doc in secrets:
            secret = doc["word"]
            if best_secret := get_best_secret(secret):
                return best_secret


def get_best_secret(secret: str) -> str:
    inp = input(f"I chose {secret[::-1]}. Ok? [Ny] > ")
    if inp in "nN":
        return ""
    if inp in ("y", "Y"):
        return secret
    else:
        return get_best_secret(inp)


if __name__ == "__main__":
    asyncio.run(main())
