
#!/usr/bin/env python3.7

import json
import sys
import os
import time
import traceback

import tornado.escape
import tornado.gen
import tornado.web

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado.web import Application

from intents_analysis import IntentCommonsense


define('port', default=9987, help='port to listen on')

if __name__ == '__main__':
    """Create and start the server. Makes it available via localhost:9989"""
   
    app = Application([
        ('/intent', IntentHandler)
    ])
    http_server = HTTPServer(app)
    http_server.listen(options.port)
    print('Listening on http://localhost:%i' % options.port)
    IOLoop.current().start()


class InputRequest(object):
    """
    Input request as defined in the requirements.
    """
    def __init__(self, sentence):
        self.sentence = sentence

class OutputRequest(object):
    """
    Input request as defined in the requirements.
    """
    def __init__(self, intents):
        self.intents = intents
        
    def get_data(self):
        return self.__dict__

class IntentHandler(tornado.web.RequestHandler):

    def set_default_headers(self, *args, **kwargs):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "*")
        self.intent = IntentCommonsense()

    def _return_response(self, request, message_to_be_returned, status_code):
        """
        Returns formatted response back to client
        """
        try:
            request.set_header("Content-Type", "application/json; charset=UTF-8")
            request.set_status(status_code)

            #If dictionary is not empty then write the dictionary directly into
            if(bool(message_to_be_returned)):
                request.write(message_to_be_returned)

            request.finish()
        except Exception:
            raise

    def prepare(self):
        print("Message received.")

    def data_received(self, chunk):
        print("Data received.", chunk)

    def get(self):
        print("GET: Received!")

    def post(self):
        """
        This function parses the request body and does something
        """
        try:
            t = time.time()
            request_payload = tornado.escape.json_decode(self.request.body)
            input = InputRequest(sentence=request_payload)

            intents = self.intent.predict(input.sentence)

            output = OutputRequest(
                intents=intents
            )

            print('Total time. (%.3fs)' % (time.time() - t))
            return self._return_response(self, message_to_be_returned=tornado.escape.json_encode(output.get_data()), status_code=200)

        except json.decoder.JSONDecodeError:
            return self._return_response(self, { "message": 'Cannot decode request body!' }, 400)

        except Exception as ex:
            return self._return_response(self, { "message": 'Could not complete the request because of some error at the server!', "cause": ex.args[0], "stack_trace": traceback.format_exc(sys.exc_info()) }, 500)

