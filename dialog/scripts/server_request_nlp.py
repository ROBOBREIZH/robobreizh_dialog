import argparse

import numpy as np
import tornado.escape
import tornado.httpclient
import tornado.ioloop
import tornado.web


class MainHandler(tornado.web.RequestHandler):
    def post(self):
        data = self.get_argument('body', 'No data received')
        self.write(data)


application = tornado.web.Application([
    (r"/", MainHandler),
])
application.listen(8890)


class ServerRequestNLP:
    def __init__(self):
        #self.http = "https://www.enib.fr/~robobreizh/robocup.php"
        self.http = "http://192.168.11.199:9988/nlp"
        self.http_client = tornado.httpclient.HTTPClient(defaults=dict(request_timeout=180))
        #tornado.ioloop.IOLoop.instance().start()

    def prepare_request(self, sentence):
        input = ""
        input = sentence

        return input

    def request(self, sentence):

        body = tornado.escape.json_encode(sentence)  # Make it into a post request
        response = self.http_client.fetch(self.http, method='POST', headers=None, body=body)
        output = tornado.escape.json_decode(response.body)
        #tornado.ioloop.IOLoop.instance().start()
       
        #output["isBag", "isChairEmpty","isChairTaken","isWaving","isPerson","features"]
        #print(body["features"])
        return output
