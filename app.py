#!/usr/bin/env python
from datetime import datetime, timedelta
import os
import uuid

import tornado.httpserver
import tornado.ioloop
import tornado.web

from common import config
from common.logger import logger
from common.session import get_mongo
from common.session import get_redis
import handlers


class WebApp(tornado.web.Application):
    PATH = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = config.api_key
        self.main_quote = config.quotes[0]
        self.quotes = config.quotes[1:]
        self.js_version = uuid.uuid4().hex[:6]


static_handlers = [
    (
        r"/css/(.*)",
        tornado.web.StaticFileHandler,
        {"path": WebApp.PATH + "/static/css"},
    ),
    (
        r"/color/(.*)",
        tornado.web.StaticFileHandler,
        {"path": WebApp.PATH + "/static/color"},
    ),
    (
        r"/font-awesome/(.*)",
        tornado.web.StaticFileHandler,
        {"path": WebApp.PATH + "/static/font-awesome"},
    ),
    (
        r"/js/(.*)",
        tornado.web.StaticFileHandler,
        {"path": WebApp.PATH + "/static/js"},
    ),
    (
        r"/(favicon.ico|menu.html)",
        tornado.web.StaticFileHandler,
        {"path": WebApp.PATH + "/static/"},
    ),
]

if __name__ == "__main__":
    handlers = handlers.get_handlers()
    handlers.extend(static_handlers)
    app = WebApp(handlers)
    http_server = tornado.httpserver.HTTPServer(app)
    port = int(os.environ["PORT"])
    num_processes = int(os.environ.get("NUM_PROCESSES", 1))
    http_server.bind(port)
    http_server.start(num_processes)
    app.mongo = get_mongo()
    app.redis = get_redis()
    app.limit = int(os.environ.get("LIMIT", 10))
    app.period = int(os.environ.get("PERIOD", 20))
    app.videos = config.videos
    try:
        date = datetime.strptime(os.environ.get("GAME_DATE", ""), '%Y-%m-%d').date()
        delta = (datetime.utcnow().date() - date).days
    except ValueError:
        delta = 0
    app.days_delta = delta

    while True:
        logger.warning("Running app on port %d", port)
        try:
            tornado.ioloop.IOLoop.current().start()
        except Exception as ex:
            logger.exception(ex)
            pass
