from datetime import datetime
from datetime import timedelta
import json
import tornado.web

from common.session import get_mongo
from common.session import get_redis
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
    DELTA = timedelta()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo = get_mongo()
        self.redis = get_redis()
        self.date = datetime.utcnow().date() - self.DELTA
        self.logic = VectorLogic(self.mongo, self.date)
        secret = self.logic.secret_logic.get_secret()
        self.cache_logic = CacheSecretLogic(
            self.mongo, self.redis, secret=secret, dt=self.date
        )

    def reply(self, content):
        content = json.dumps(content)
        self.set_header("Content-Type", "application/json")
        self.set_header("Content-Length", len(content))
        self.write(content)
        self.finish()


class IndexHandler(BaseHandler):
    FIRST_DATE = datetime(2022, 2, 21).date()

    def get(self):
        cache = self.cache_logic.cache
        closest1 = self.logic.get_similarity(cache[-2])
        closest10 = self.logic.get_similarity(cache[-12])
        closest1000 = self.logic.get_similarity(cache[0])
        number = (self.date - self.FIRST_DATE).days + 1

        yestersecret = VectorLogic(
            self.mongo, self.date - timedelta(days=1)
        ).secret_logic.get_secret()

        self.render(
            'static/index.html',
            number=number,
            closest1=closest1,
            closest10=closest10,
            closest1000=closest1000,
            yesterdays_secret=yestersecret,
        )


class DistanceHandler(BaseHandler):
    def get(self):
        word = self.get_argument('word')
        word = word.replace("'", "")
        if egg := EasterEggLogic.get_easter_egg(word):
            reply = {
                "similarity": 99.99,
                "distance": -1,
                "egg": egg
            }
        else:
            sim = self.logic.get_similarity(word)
            cache_score = self.cache_logic.get_cache_score(word)
            reply = {
                "similarity": sim,
                "distance": cache_score,
            }
        self.reply(reply)


class YesterdayClosestHandler(BaseHandler):
    DELTA = timedelta(days=1)

    def get(self):
        yesterday_sims = self.logic.get_similarities(self.cache_logic.cache)
        self.render(
            'static/closest1000.html',
            yesterday=sorted(yesterday_sims.items(), key=lambda ws: ws[1], reverse=1),
        )


class AllSecretsHandler(BaseHandler):
    def get(self):
        secrets = self.logic.secret_logic.get_all_secrets()
        api_key = self.get_argument('api_key', None)
        if api_key != self.application.api_key:
            raise tornado.web.HTTPError(403)

        self.render(
            'static/all_secrets.html',
            secrets=sorted(secrets, key=lambda ws: ws[1], reverse=1),
        )


class FaqHandler(BaseHandler):
    DELTA = timedelta(days=1)

    def get(self):
        self.render(
            'static/faq.html',
            yesterday=self.cache_logic.cache[-11:],
        )
