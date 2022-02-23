#!/usr/bin/env python
import os

import tornado.httpserver
import tornado.ioloop
import tornado.web

from common.logger import logger
from common.session import get_mongo
from common.session import get_redis
import handlers


class WebApp(tornado.web.Application):
    PATH = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, *args, **kwargs):
        self.mongo = get_mongo()
        self.redis = get_redis()
        super(WebApp, self).__init__(*args, **kwargs)


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
]


if __name__ == "__main__":
    handlers = handlers.get_handlers()
    handlers.extend(static_handlers)
    app = WebApp(handlers)
    http_server = tornado.httpserver.HTTPServer(app)
    port = int(os.environ["PORT"])
    http_server.listen(port)

    while True:
        logger.warning("Running app on port %d", port)
        try:
            tornado.ioloop.IOLoop.current().start()
        except Exception as ex:
            logger.exception(ex)
            pass
