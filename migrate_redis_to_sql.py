# type: ignore
import datetime
import re

from sqlmodel import select

from common import tables
from common.session import get_redis
from common.session import get_session
from common.session import hs_transaction

redis = get_redis()
db_session = get_session()

REDIS_RE_KEY = re.compile(r"hs:([\u0590-\u05fe]+):(\d{4}-\d{2}-\d{2})")


async def migrate():
    print("Fetching keys from")
    keys = await redis.keys()
    print(f"Found {len(keys)} keys in Redis")

    for key in keys:
        match = REDIS_RE_KEY.match(key)
        date = datetime.datetime.strptime(match.group(2), "%Y-%m-%d").date()
        secret = match.group(1)

        closest1000 = []
        closest_words = await redis.lrange(key, 0, -1)
        assert len(closest_words) == 1000
        for out_of, closest in enumerate(closest_words, start=1):
            closest1000.append(tables.Closest1000(word=closest, out_of_1000=out_of))
        t0 = datetime.datetime.now()
        print("Adding closest1000 for {}".format(secret))
        with hs_transaction(session=db_session, expire_on_commit=False) as session:
            secret_word = session.execute(
                select(tables.SecretWord).where(tables.SecretWord.game_date == date)
            ).scalar_one()
            secret_word.closest1000 = closest1000
            session.add(secret_word)
        print(f"Took {(datetime.datetime.now() - t0).seconds:.2f}")


import asyncio

asyncio.run(migrate())
