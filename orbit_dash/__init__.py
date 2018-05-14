import os

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer

from .app import flask_app


def run_server():
    http_server = HTTPServer(WSGIContainer(flask_app))
    port = int(os.environ.get("PORT", 5000))
    http_server.listen(port)
    IOLoop.instance().start()
