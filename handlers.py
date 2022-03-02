from datetime import datetime
from datetime import timedelta
import json
import tornado.web

from common.session import get_mongo
from common.session import get_redis
from logic import CacheSecretLogic
from logic import SecretLogic
from logic import VectorLogic


def get_handlers():
    return [
        (r"/?", IndexHandler),
        (r"/yesterday-top-1000/?", YesterdayClosestHandler),
        (r"/api/distance/?", DistanceHandler),
        (r"/secrets/?", AllSecretsHandler),
    ]


class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo = get_mongo()
        self.redis = get_redis()
        date = datetime.utcnow().date()
        self.logic = VectorLogic(self.mongo, date)
        secret = self.logic.secret_logic.get_secret()
        self.cache_logic = CacheSecretLogic(self.mongo, self.redis, secret=secret, dt=date)

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

        todate = datetime.utcnow().date()
        yesterdate = todate - timedelta(days=1)
        yesterday_secret = SecretLogic(self.mongo, yesterdate).get_secret()
        yesterday_cache = CacheSecretLogic(
            self.mongo, self.redis, secret=yesterday_secret, dt=yesterdate,
        ).cache
        number = (todate - self.FIRST_DATE).days + 1
        self.render(
            'static/index.html',
            number=number,
            closest1=closest1,
            closest10=closest10,
            closest1000=closest1000,
            yesterday=yesterday_cache[-11:],
        )


class DistanceHandler(BaseHandler):
    def get(self):
        word = self.get_argument('word')
        word = word.replace("'", "")
        sim = self.logic.get_similarity(word)
        cache_score = self.cache_logic.get_cache_score(word)

        self.reply(
            {
                "similarity": sim,
                "distance": cache_score,
            }
        )


class YesterdayClosestHandler(BaseHandler):
    def get(self):
        todate = datetime.utcnow().date()
        yesterdate = todate - timedelta(days=1)
        logic = VectorLogic(self.mongo, dt=yesterdate)
        yesterday_secret = logic.secret_logic.get_secret()
        yesterday_cache = CacheSecretLogic(
            self.mongo, self.redis, secret=yesterday_secret, dt=yesterdate,
        ).cache

        yesterday_sims = logic.get_similarities(yesterday_cache)

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

