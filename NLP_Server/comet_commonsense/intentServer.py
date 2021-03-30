from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado.web import Application

from intentHandler import IntentHandler

define('port', default=9987, help='port to listen on')

def main():
    """Create and start the server. Makes it available via localhost:9989"""
   
    app = Application([
        ('/intent', IntentHandler)
    ])
    http_server = HTTPServer(app)
    http_server.listen(options.port)
    print('Listening on http://localhost:%i' % options.port)
    IOLoop.current().start()


if __name__ == '__main__':
    main()