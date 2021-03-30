import argparse
import base64

import cv2
import numpy as np
import tornado.escape
import tornado.httpclient
import tornado.ioloop
import tornado.web



class ServerRequestVis:
    def __init__(self):
        #self.http = "https://www.enib.fr/~robobreizh/robocup.php"
        self.http = "http://192.168.11.199:9989/robocup"
        self.http_client = tornado.httpclient.HTTPClient(defaults=dict(request_timeout=180))
        #tornado.ioloop.IOLoop.instance().start()

    def prepare_request(self, arr_image, option):
        input = {}
        input["image"] = self.cv2_to_base64(arr_image).decode('utf-8')
        #pour activer / desactiver la detection de mouvement
        #par defaut, toutes les detections sont actives
        input["isMovement"] = False
        input["onlyMovement"] = False
        input["features"] = False

        if option == "allDetection":
            input["isMovement"] = True
        elif option == "onlyMovement":
            input["onlyMovement"] = True
            input["isMovement"] = True
        elif option == "onlyFeatures":
            input["features"] = True
        elif option == "personDetect":
            input["features"] = True
            input["isMovement"] = True


        #pour activer UNIQUEMENT la detection de mouvement
        return input

    def request(self, cv2_img, option):

        body = tornado.escape.json_encode(self.prepare_request(cv2_img, option))  # Make it into a post request
        response = self.http_client.fetch(self.http, method='POST', headers=None, body=body)
        output = tornado.escape.json_decode(response.body)
        #tornado.ioloop.IOLoop.instance().start()
       
        #output["isBag", "isChairEmpty","isChairTaken","isWaving","isPerson","features"]
        #print(body["features"])
        return output

    def cv2_to_base64(self, arr_cv2):
        result, dst_data = cv2.imencode('.jpg', arr_cv2)
        str_base64 = base64.b64encode(dst_data)
        return str_base64

    def base64_to_cv2(eself, encoded_data):
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

