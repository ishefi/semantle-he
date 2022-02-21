from datetime import datetime
from datetime import timedelta
import json
import tornado.web

from logic import CacheSecretLogic
from logic import SecretLogic
from logic import VectorLogic


def get_handlers():
    return [
        (r"/?", IndexHandler),
        (r"/api/distance/?", DistanceHandler),
    ]


class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_factory = self.application.session_factory
        self.redis = self.application.redis
        self.logic = VectorLogic(self.session_factory)
        secret = self.logic.secret_logic.get_secret()
        date = datetime.utcnow().date()
        self.cache_logic = CacheSecretLogic(self.session_factory, self.redis, secret=secret, dt=date)

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

        yesterdate = datetime.utcnow().date() - timedelta(days=1)
        yesterday_secret = SecretLogic(
            self.session_factory, yesterdate
        ).get_secret()
        yesterday_cache = CacheSecretLogic(
            self.session_factory, self.redis, secret=yesterday_secret, dt=yesterdate,
        ).cache
        number = (self.FIRST_DATE - yesterdate).days
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
        sim = self.logic.get_similarity(word)
        cache_score = self.cache_logic.get_cache_score(word)

        self.reply(
            {
                "similarity": sim,
                "distance": cache_score,
            }
        )




