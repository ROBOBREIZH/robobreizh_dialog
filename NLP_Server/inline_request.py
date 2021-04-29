import time
import numpy as np

#import rospy
# from geometry_msgs.msg import Twist
# from std_msgs.msg import String
# from mbot_nlu.msg import ActionSlotArray

#import cv2, random, time, base64
#from cv_bridge import CvBridge, CvBridgeError

import imutils
import socket
import json

from topic_extraction import Extractor
from NLPModule import NLPModule

import os
import sys
import argparse
import torch

sys.path.append(os.getcwd()+'/comet_commonsense')

import src.data.data as data
import src.data.config as cfg
import src.interactive.functions as interactive

import socket
import json
import speech_recognition as sr
from gtts import gTTS
from audioplayer import AudioPlayer

class Request():
	def __init__(self):
		#self.bridge = CvBridge()

		#node = rospy.init_node('InteractionModule')

		self.dialog_topic = ""

		self.server_ip = '127.0.0.1'
		self.server_port = 9987
		self.server_ip_intents = '127.0.0.1'
		self.server_port_intents = 9986

	def socket_request(self, sentence):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((self.server_ip_intents, self.server_port_intents))
		#print("Connection on {}".format(port))
		sock.send(sentence)
		res = sock.recv(9999999)
		res_dict = json.loads(res.decode('utf-8'))
		sock.close()
		return res_dict


	def socket_request_sentence_analysis(self, sentence):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((self.server_ip, self.server_port))
		print("Request category and sentiment analysis . . . \n")

		#print("Connection on {}".format(port))
		sock.send(sentence)
		res = sock.recv(9999999)
		res_dict = json.loads(res.decode('utf-8'))
		sock.close()
		return res_dict

	def action_command(self, command):
		seconds = time.time()
		self.pub = rospy.Publisher('hri/nlu/mbot_nlu/input_sentence', String,  queue_size=10)
		rospy.sleep(1)
		self.pub.publish(command)

		msg = rospy.wait_for_message('hri/nlu/mbot_nlu/output_recognition', ActionSlotArray) 

		duration = time.time() - seconds

		return msg

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

def main():
	test = Extractor()
	nlp = NLPModule()
	req = Request()

	question = input("Enter a question, tape 'end' to finish \n")

	while not question == "end":
		
		main_topic, sentence = test.extract(str(question))

		print(f"{bcolors.OKGREEN} \n New sentence : {bcolors.ENDC} {sentence} \n")
		print(f"{bcolors.OKGREEN} \n Main topic : {bcolors.ENDC} {main_topic} \n")

		category = nlp.find_category(question)
		print(f"{bcolors.OKGREEN} \n Sentence category : {bcolors.ENDC} {category} \n")

		sentiment = nlp.sentiment_analysis(question)
		print(f"{bcolors.OKGREEN} \n Sentiment : {bcolors.ENDC} mainly {sentiment} \n")

		intents = req.socket_request(str.encode(question))

		print(f"{bcolors.OKGREEN}\n Intentions analysis \n{bcolors.ENDC}")

		print(f" I view the user as {intents['relation']}")

		print(f" The user intents is {intents['intends']}")

		print(f" The user desire is {intents['desire']}")

		print(f" The user need {intents['needs']}")

		print(f" I believe the user intent is used for {intents['utility']}")

		print(f" I believe the expected outcome is a {intents['type']} \n")

		question = input("Enter a question, tape 'end' to finish \n")

def mainMicrophone():
	r = sr.Recognizer()
	test = Extractor()
	nlp = NLPModule()
	req = Request()

	print("Ready, speak \n ")

	while True:
		with sr.Microphone() as source:
			r.adjust_for_ambient_noise(source) 
			print("Say something!")
			audio = r.listen(source)
			transcript=""
			try:
				transcript = r.recognize_google(audio)
			except:
				print("Can't understand")

			if transcript == "":
				continue
			print("Recognize: "+transcript)

			question = transcript		
			main_topic, sentence = test.extract(str(question))

			print(f"{bcolors.OKGREEN} \n New sentence : {bcolors.ENDC} {sentence} \n")
			print(f"{bcolors.OKGREEN} \n Main topic : {bcolors.ENDC} {main_topic} \n")

			category = nlp.find_category(question)
			print(f"{bcolors.OKGREEN} \n Sentence category : {bcolors.ENDC} {category} \n")

			sentiment = nlp.sentiment_analysis(question)
			print(f"{bcolors.OKGREEN} \n Sentiment : {bcolors.ENDC} mainly {sentiment} \n")

			intents = req.socket_request(str.encode(question))

			print(f"{bcolors.OKGREEN}\n Intentions analysis \n{bcolors.ENDC}")

			print(f" I view the user as {intents['relation']}")

			print(f" The user intents is {intents['intends']}")

			print(f" The user desire is {intents['desire']}")

			print(f" The user need {intents['needs']}")

			print(f" I believe the user intent is used for {intents['utility']}")

			print(f" I believe the expected outcome is a {intents['type']} \n")

			text = "I think you are "+str(intents['relation'])
			text += " and you want to "+str(intents['desire'])
			text += " because it's a "+str(intents['type'])

			language = 'en'
			myobj = gTTS(text=text, lang=language, slow=False)

			myobj.save("test.mp3")
			AudioPlayer("test.mp3").play(block=True)


			

if __name__ == '__main__':
	mainMicrophone()