from datetime import datetime
import os
import sys

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

from common.session import get_redis
from common.session import get_mongo
from logic import VectorLogic
from logic import CacheSecretLogic


def main():
    print("Welcome! Take a guess:")
    inp = None
    mongo = get_mongo()
    redis = get_redis()
    date = datetime.utcnow().date()
    logic = VectorLogic(mongo, date)
    secret = logic.secret_logic.get_secret()
    cache_logic = CacheSecretLogic(mongo, redis, secret=secret, dt=date)
    while inp != 'exit':
        if datetime.utcnow().date() != date:
            date = datetime.utcnow().date()
            logic = VectorLogic(mongo, date)
            secret = logic.secret_logic.get_secret()
            cache_logic = CacheSecretLogic(mongo, redis, secret=secret, dt=date)
        inp = input('>')
        print(inp[::-1])
        distance = logic.get_similarity(inp)
        if distance < 0:
            print("I don't know this word!")
        else:
            cache_score = cache_logic.get_cache_score(inp)
            if cache_score < 0:
                cache_data = '(cold)'
            else:
                cache_data = f'{cache_score}/1000'
            print(f"Distance: {distance} | {cache_data}")


if __name__ == '__main__':
    main()
