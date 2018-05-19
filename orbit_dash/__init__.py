import os

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer

from .app import flask_app, dash_app


def run_server(debug=False, port=5000):
    if debug:
        dash_app.run_server(debug=True, port=port)
    else:
        http_server = HTTPServer(WSGIContainer(flask_app))
        port = int(os.environ.get("PORT", port))
        http_server.listen(port)
        IOLoop.instance().start()
