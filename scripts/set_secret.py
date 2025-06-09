#!/usr/bin/env python
from __future__ import annotations

import asyncio
import datetime
import os
import random
import sys
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from typing import TYPE_CHECKING

from sqlmodel import select

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

from common import tables  # noqa: E402
from common.session import get_model  # noqa: E402
from common.session import get_session  # noqa: E402
from common.session import hs_transaction  # noqa: E402
from logic.game_logic import CacheSecretLogic  # noqa: E402

if TYPE_CHECKING:
    from sqlmodel import Session

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
    parser.add_argument(
        "--top-sample",
        default=10000,
        type=int,
        help="Top n words to choose from when choosing a random word. If not provided, will use all words in the model.",
    )

    args = parser.parse_args()

    session = get_session()
    model = get_model()

    if args.date:
        date = args.date
    else:
        date = await get_date(session)
    if args.secret:
        secret = args.secret
    else:
        secret = await get_random_word(model, args.top_sample)
    while True:
        if await do_populate(session, secret, date, model, args.force, args.top_sample):
            if not args.iterative:
                break
            date += datetime.timedelta(days=1)
            print(f"Now doing {date}")
        secret = await get_random_word(model, args.top_sample)


async def get_date(session: Session) -> datetime.date:
    query = select(tables.SecretWord.game_date)  # type: ignore
    query = query.order_by(tables.SecretWord.game_date.desc())  # type: ignore
    with hs_transaction(session) as s:
        latest: datetime.date = s.exec(query).first()

    dt = latest + datetime.timedelta(days=1)
    print(f"Now doing {dt}")
    return dt


async def do_populate(
    session: Session,
    secret: str,
    date: datetime.date,
    model: GensimModel,
    force: bool,
    top_sample: int | None,
) -> bool:
    logic = CacheSecretLogic(session, secret, dt=date, model=model)
    try:
        await logic.simulate_set_secret(force=force)
    except ValueError as err:
        print(err)
        return False
    cache = [w[::-1] for w in (await logic.get_cache())[::-1]]
    print(" ,".join(cache))
    print(cache[0])
    for rng in (range(i, i + 10) for i in [1, 50, 100, 300, 550, 750]):
        for i in rng:
            w = cache[i]
            print(f"{i}: {w}")
    pop = input("Populate?\n")
    if pop in ("y", "Y"):
        hot_clues = input("Clues? Space separated\n")
        clues = []
        for hot_clue in hot_clues.split(" "):
            if input(f"Add clue?\n{hot_clue[::-1]}\n[Yn] > ").lower() == "n":
                continue
            else:
                clues.append(hot_clue)
        await logic.do_populate(clues)
        print("Done!")
        return True
    else:
        secret = await get_random_word(model, top_sample)  # TODO: use model
        return await do_populate(session, secret, date, model, force, top_sample)


async def get_random_word(model: GensimModel, top_sample: int | None) -> str:
    while True:
        if top_sample is None:
            top_sample = len(model.model.index_to_key)
        rand_index = random.randint(0, top_sample)
        if best_secret := get_best_secret(model.model.index_to_key[rand_index]):
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
