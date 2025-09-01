# type: ignore
import asyncio
from argparse import ArgumentParser
from datetime import date
from datetime import datetime
from datetime import timedelta
from sqlite3 import OperationalError
from typing import TypeVar

import requests
from sqlmodel import select
from tqdm import tqdm

from common import config
from common import tables
from common.session import get_mongo
from common.session import get_session
from common.session import hs_transaction

SESSION = get_session()

USER_CACHE = {}

T = TypeVar("TV")


def batches(iterable: list[T], n=1) -> T:
    l = len(iterable)
    return list(iterable[i : i + n] for i in range(0, l, n))


async def _do_it(date: date, skip: int, batch_size: int, only_verify: bool) -> None:
    mongo_users = get_mongo().users
    history = f"history.{date}"
    cursor = mongo_users.find(
        {history: {"$exists": True}},
        {"email": 1, history: 1},
    )
    cursor.skip(skip)
    users = await cursor.to_list(length=None)
    for i, user in (
        bar := tqdm(enumerate(users, start=1), initial=skip, total=len(users) + skip)
    ):
        bar.set_description(str(date))
        if i % 500 == 0:
            requests.post(
                config.alerts_webhook,
                json={"text": f"Migration alert: {date} - {i+skip}/{len(users)+skip}"},
            )
        if user["email"] in USER_CACHE:
            user_id = USER_CACHE[user["email"]]
        else:
            with hs_transaction(SESSION) as session:
                query = select(tables.User.id).where(tables.User.email == user["email"])
                user_id = session.exec(query).first()
                # if not user_id or user_id < 0:
                #     requests.post(config.alerts_webhook, json={"text": "BAD USER: " +user["email"]})
                #     continue
                assert isinstance(user_id, int) and user_id > 0
                USER_CACHE[user["email"]] = user_id
        histories = user.get("history", {}).get(str(date), [])
        if not histories:
            continue
        else:
            guess_to_hist = {history["guess"]: history for history in histories}
            with hs_transaction(SESSION) as session:
                history_query = select(tables.UserHistory.guess).where(
                    tables.UserHistory.user_id == user_id,
                    tables.UserHistory.game_date == date,
                    tables.UserHistory.guess.in_(
                        history["guess"] for history in histories
                    ),
                )
                db_histories = session.exec(history_query).all()
                for db_history_guess in db_histories:
                    guess_to_hist.pop(db_history_guess)
            if not guess_to_hist:
                continue
            if only_verify:
                assert not guess_to_hist, guess_to_hist
            for batch in tqdm(batches(list(guess_to_hist.values()), batch_size)):
                with hs_transaction(SESSION) as session:
                    for history in batch:
                        session.add(
                            tables.UserHistory(
                                user_id=user_id, game_date=date, **history
                            )
                        )
    # for game_date, histories in user.get("history", {}).items():
    #     print(f"Doing history for user {user_id} - {user['email']} (total {len(histories)})")
    #     game_dt = datetime.strptime(game_date, "%Y-%m-%d").date()
    #     for i, history in enumerate(histories, start=1):
    #         if i % 10 == 0:
    #             print(f"Done {i} of {len(histories)}")
    #         with hs_transaction(SESSION) as session:
    #             db_history = session.query(tables.UserHistory).filter(
    #                 tables.UserHistory.user_id == user_id,
    #                 tables.UserHistory.game_date == game_dt,
    #                 tables.UserHistory.guess == history["guess"],
    #             ).first()
    #             if db_history is not None:
    #                 continue
    #             session.add(tables.UserHistory(
    #                 user_id=user_id,
    #                 game_date=game_dt,
    #                 **history,
    #                 )
    #             )
    # for clue_date, clue_count in user.get("clues", {}).items():
    #     clue_dt = datetime.strptime(clue_date, "%Y-%m-%d").date()
    #     with hs_transaction(SESSION) as session:
    #         if session.query(tables.UserClueCount).filter(
    #             tables.UserClueCount.user_id == user_id,
    #             tables.UserClueCount.game_date == clue_dt,
    #         ).first() is not None:
    #             continue
    #         session.add(tables.UserClueCount(
    #             user_id=user_id,
    #             clue_count=clue_count,
    #             game_date=clue_dt,
    #         ))


async def do_it_outer() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "--min-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        required=True,
    )
    parser.add_argument(
        "--max-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(),
        required=True,
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=15,
    )
    parser.add_argument(
        "--only-verify",
        action="store_true",
    )
    args = parser.parse_args()
    max_day = args.max_date
    day = args.min_date
    skip = args.skip  # first skip
    await do_it(day, max_day, skip, args.batch_size, args.only_verify)


async def do_it(day, max_day, skip, batch_size, only_verify) -> None:
    delta = max_day - day

    assert delta.days > 0

    for day in tqdm([day + timedelta(days=i) for i in range(delta.days)]):
        print(f"DOING {day}")
        success = False
        try:
            await _do_it(
                date=day, skip=skip, batch_size=batch_size, only_verify=only_verify
            )
            skip = 0
            success = True
        except TimeoutError:
            print("=====================================")
            print("TIMEOUT")
            print("=====================================")
            return
        except OperationalError:
            print("=====================================")
            print("OPERROR")
            print("=====================================")
            return
        except KeyboardInterrupt:
            return
        except:
            print(f"FAILED {day}")
            raise
        finally:
            marker = "✅" if success else "❌"
            msg = f"{'Done' if success else 'Failed'} {day}"
            print(marker * 20)
            print(marker * 20)
            print(msg)
            print(f"At - {datetime.now(datetime.UTC)}")
            print(marker * 20)
            print(marker * 20)
            requests.post(
                config.alerts_webhook, json={"text": f"Migration alert: {marker}{msg}"}
            )


asyncio.run(do_it_outer())
