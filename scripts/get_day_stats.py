#!/usr/bin/env python
import os
import sys

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

import argparse
import datetime

from common.session import get_model
from common.session import get_session
from logic.game_logic import CacheSecretLogic
from logic.game_logic import VectorLogic
from logic.user_logic import UserClueLogic


def valid_date(date_str: str) -> datetime.date:
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError("Bad date: should be of the format YYYY-mm-dd")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--date",
        metavar="DATE",
        type=valid_date,
        required=True,
        help="Date of secret. If not provided, first date w/o secret is used",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    session = get_session()
    model = get_model()
    logic = VectorLogic(session, dt=args.date, model=model)
    secret = await logic.secret_logic.get_secret()

    cache_logic = CacheSecretLogic(
        session=session,
        secret=secret,
        dt=args.date,
        model=model,
    )

    cache_len = len(await cache_logic.get_cache())

    clue_logic = UserClueLogic(
        session=session,
        user=None,  # type: ignore[arg-type]
        secret=secret,
        date=args.date,
    )
    clues = clue_logic.clues

    print(f"Word for {args.date}: {secret}")
    print(f"{cache_len} cached words and {len(clues)} clues")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
