import asyncio
from datetime import datetime
import os
import sys

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

from common.session import get_redis, get_model
from common.session import get_mongo
from logic.game_logic import VectorLogic
from logic.game_logic import CacheSecretLogic


async def main():
    print("Welcome! Take a guess:")
    inp = None
    mongo = get_mongo()
    redis = get_redis()
    model = get_model(mongo)
    date = datetime.utcnow().date()
    logic = VectorLogic(mongo, dt=date, model=model)
    secret = await logic.secret_logic.get_secret()
    cache_logic = CacheSecretLogic(mongo, redis, secret=secret, dt=date, model=model)
    while inp != 'exit':
        if datetime.utcnow().date() != date:
            date = datetime.utcnow().date()
            logic = VectorLogic(mongo, dt=date, model=model)
            secret = await logic.secret_logic.get_secret()
            cache_logic = CacheSecretLogic(mongo, redis, secret=secret, dt=date, model=model)
        inp = input('>')
        print(inp[::-1])
        similarity = await logic.get_similarity(inp)
        if similarity < 0:
            print("I don't know this word!")
        else:
            cache_score = await cache_logic.get_cache_score(inp)
            if cache_score < 0:
                cache_data = '(cold)'
            else:
                cache_data = f'{cache_score}/1000'
            print(f"Distance: {similarity} | {cache_data}")


if __name__ == '__main__':
    asyncio.run(main())
