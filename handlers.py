from datetime import datetime
from datetime import timedelta
import json
import random

import tornado.web

from logic import CacheSecretLogic
from logic import EasterEggLogic
from logic import VectorLogic


def get_handlers():
    return [
        (r"/?", IndexHandler),
        (r"/yesterday-top-1000/?", YesterdayClosestHandler),
        (r"/api/distance/?", DistanceHandler),
        (r"/secrets/?", AllSecretsHandler),
        (r"/faq/?", FaqHandler),
    ]


class BaseHandler(tornado.web.RequestHandler):
    _DELTA = None
    _SECRET_CACHE = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo = self.application.mongo
        self.redis = self.application.redis
        self.date = datetime.utcnow().date() - self.DELTA
        self.logic = VectorLogic(self.mongo, self.date)
        secret = self.logic.secret_logic.get_secret()
        self.cache_logic = CacheSecretLogic(
            self.mongo, self.redis, secret=secret, dt=self.date
        )

    @property
    def DELTA(self):
        if self._DELTA is None:
            self._DELTA = timedelta(days=self.application.days_delta)
        return self._DELTA

    async def reply(self, content):
        content = json.dumps(content)
        self.set_header("Content-Type", "application/json")
        self.set_header("Content-Length", len(content))
        self.write(content)
        await self.finish()


class IndexHandler(BaseHandler):
    FIRST_DATE = datetime(2022, 2, 21).date()

    async def get(self):
        cache = await self.cache_logic.cache
        closest1 = await self.logic.get_similarity(cache[-2])
        closest10 = await self.logic.get_similarity(cache[-12])
        closest1000 = await self.logic.get_similarity(cache[0])
        number = (self.date - self.FIRST_DATE).days + 1

        yestersecret = await VectorLogic(
            self.mongo, self.date - timedelta(days=1)
        ).secret_logic.get_secret()

        if random.random() >= 0.5:
            quote = self.application.main_quote
        else:
            quote = random.choice(self.application.quotes)

        await self.render(
            'static/index.html',
            number=number,
            closest1=closest1,
            closest10=closest10,
            closest1000=closest1000,
            yesterdays_secret=yestersecret,
            quote=quote,
        )


class DistanceHandler(BaseHandler):
    async def get(self):
        word = self.get_argument('word')
        word = word.replace("'", "")
        if egg := EasterEggLogic.get_easter_egg(word):
            reply = {
                "similarity": 99.99,
                "distance": -1,
                "egg": egg
            }
        else:
            sim = await self.logic.get_similarity(word)
            cache_score = await self.cache_logic.get_cache_score(word)
            reply = {
                "similarity": sim,
                "distance": cache_score,
            }
        await self.reply(reply)


class YesterdayClosestHandler(BaseHandler):
    async def get(self):
        cache = await self.cache_logic.cache
        yesterday_sims = await self.logic.get_similarities(cache)
        await self.render(
            'static/closest1000.html',
            yesterday=sorted(yesterday_sims.items(), key=lambda ws: ws[1], reverse=1),
        )

    @property
    def DELTA(self):
        return super().DELTA + timedelta(days=1)

class AllSecretsHandler(BaseHandler):
    async def get(self):
        secrets = await self.logic.secret_logic.get_all_secrets()
        api_key = self.get_argument('api_key', None)
        if api_key != self.application.api_key:
            raise tornado.web.HTTPError(403)

        await self.render(
            'static/all_secrets.html',
            secrets=sorted(secrets, key=lambda ws: ws[1], reverse=1),
        )


class FaqHandler(BaseHandler):
    DELTA = timedelta(days=1)

    async def get(self):
        cache = await self.cache_logic.cache
        await self.render(
            'static/faq.html',
            yesterday=cache[-11:],
        )
