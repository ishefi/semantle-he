#!/usr/bin/env python
import os

import tornado.httpserver
import tornado.ioloop
import tornado.web

from common import config
from common.logger import logger
import handlers


class WebApp(tornado.web.Application):
    PATH = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = config.api_key



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
        r"/(favicon.ico)",
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

    while True:
        logger.warning("Running app on port %d", port)
        try:
            tornado.ioloop.IOLoop.current().start()
        except Exception as ex:
            logger.exception(ex)
            pass
