from datetime import datetime
import json
import tornado.web

from logic import CacheSecretLogic
from logic import VectorLogic


def get_handlers():
    return [
        (r"/?", IndexHandler),
        (r"/api/distance/?", DistanceHandler),
    ]


class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        session_factory = self.application.session_factory
        redis = self.application.redis
        self.logic = VectorLogic(session_factory, redis)
        secret = self.logic.secret_logic.get_secret()
        date = datetime.utcnow().date()
        self.cache_logic = CacheSecretLogic(session_factory, redis, secret=secret, dt=date)


    def reply(self, content):
        content = json.dumps(content)
        self.set_header("Content-Type", "application/json")
        self.set_header("Content-Length", len(content))
        self.write(content)
        self.finish()


class IndexHandler(BaseHandler):
    def get(self):
        cache = self.cache_logic.cache
        closest1 = self.logic.get_similarity(cache[-2])
        closest10 = self.logic.get_similarity(cache[-12])
        closest1000 = self.logic.get_similarity(cache[0])

        self.render(
            'static/index.html',
            closest1=closest1,
            closest10=closest10,
            closest1000=closest1000,
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




