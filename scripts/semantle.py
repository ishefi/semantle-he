import asyncio
import datetime

from common.error import HSError
from common.session import get_model
from common.session import get_session
from logic.game_logic import CacheSecretLogic
from logic.game_logic import VectorLogic


def _get_todays_date() -> datetime.date:
    return datetime.datetime.now(datetime.UTC).date()


async def main() -> None:
    print("Welcome! Take a guess:")
    inp = None
    model = get_model()
    session = get_session()
    date = _get_todays_date()
    logic = VectorLogic(session, dt=date, model=model)
    secret = await logic.secret_logic.get_secret()
    cache_logic = CacheSecretLogic(session, secret=secret, dt=date, model=model)
    while inp != "exit":
        if _get_todays_date() != date:
            date = _get_todays_date()
            logic = VectorLogic(session, dt=date, model=model)
            secret = await logic.secret_logic.get_secret()
            cache_logic = CacheSecretLogic(session, secret=secret, dt=date, model=model)
        inp = input(">")
        print(inp[::-1])
        try:
            similarity = await logic.get_similarity(inp)
        except HSError:
            print("I don't know this word!")
        else:
            cache_score = await cache_logic.get_cache_score(inp)
            if cache_score < 0:
                cache_data = "(cold)"
            else:
                cache_data = f"{cache_score}/1000"
            print(f"Distance: {similarity} | {cache_data}")


if __name__ == "__main__":
    asyncio.run(main())
