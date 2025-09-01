#!/usr/bin/env python

import os
import sys

import tqdm

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

import argparse
import datetime

from sqlmodel import select

from common import tables
from common.session import get_model
from common.session import get_session
from common.session import hs_transaction
from logic.game_logic import CacheSecretLogic
from logic.game_logic import VectorLogic


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--date",
        metavar="DATE",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d").date(),
        required=True,
    )

    args = parser.parse_args()
    date = args.date

    session = get_session()
    model = get_model()

    vector_logic = VectorLogic(session=session, model=model, dt=date)
    secret = await vector_logic.secret_logic.get_secret()

    cache_logic = CacheSecretLogic(
        session=session, dt=date, model=get_model(), secret=secret
    )

    cache = await cache_logic.get_cache()
    print(f"found cache of {len(cache)} for {date} with secret {secret}")

    with hs_transaction(session) as session:
        query = select(tables.UserHistory)
        query = query.where(tables.UserHistory.game_date == date)
        query = query.where(tables.UserHistory.guess.in_(cache))  # type: ignore[attr-defined]
        query = query.where(tables.UserHistory.distance == -1)
        histories = session.exec(query).all()
        hist_to_guess = {hist.id: hist.guess for hist in histories}

    print(f"Found {len(hist_to_guess)} histories to update")
    print(hist_to_guess)

    hist_id_to_cache_and_solver_count = {}

    for hist_id, guess in tqdm.tqdm(hist_to_guess.items()):
        distance = cache.index(guess) + 1
        solver_count = await vector_logic.get_and_update_solver_count()
        hist_id_to_cache_and_solver_count[hist_id] = (distance, solver_count)

    print(hist_id_to_cache_and_solver_count)

    with hs_transaction(session) as session:
        query = select(tables.UserHistory)
        query = query.where(
            tables.UserHistory.id.in_(hist_id_to_cache_and_solver_count.keys())  # type: ignore[attr-defined]
        )
        histories = session.exec(query).all()

        for history in tqdm.tqdm(histories):
            distance, solver_count = hist_id_to_cache_and_solver_count[history.id]
            history.distance = distance
            history.solver_count = solver_count
            session.add(history)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
