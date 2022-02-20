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
    def reply(self, content):
        content = json.dumps(content)
        self.set_header("Content-Type", "application/json")
        self.set_header("Content-Length", len(content))
        self.write(content)
        self.finish()


class IndexHandler(BaseHandler):
    def get(self):
        self.render(
            'static/index.html',
            closest1=1.0,  # TODO
            closest10=10.0,  # TODO
            closest1000=1000.0,  # TODO
        )


class DistanceHandler(BaseHandler):
    def get(self):
        word = self.get_argument('word')
        session_factory = self.application.session_factory
        redis = self.application.redis
        logic = VectorLogic(session_factory, redis)
        sim = logic.get_similarity(word)
        secret = logic.secret_logic.get_secret()
        date = datetime.utcnow().date()
        cache_logic = CacheSecretLogic(session_factory, redis, secret=secret, dt=date)
        cache_score = cache_logic.get_cache_score(word)

        self.reply(
            {
                "similarity": sim,
                "distance": cache_score,
            }
        )




