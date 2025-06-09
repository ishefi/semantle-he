import asyncio
import os
import sys
from datetime import datetime

from common.error import HSError

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

from common.session import get_model  # noqa: E402
from common.session import get_session  # noqa: E402
from logic.game_logic import CacheSecretLogic  # noqa: E402
from logic.game_logic import VectorLogic  # noqa: E402


async def main() -> None:
    print("Welcome! Take a guess:")
    inp = None
    model = get_model()
    session = get_session()
    date = datetime.utcnow().date()
    logic = VectorLogic(session, dt=date, model=model)
    secret = await logic.secret_logic.get_secret()
    cache_logic = CacheSecretLogic(session, secret=secret, dt=date, model=model)
    while inp != "exit":
        if datetime.utcnow().date() != date:
            date = datetime.utcnow().date()
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
