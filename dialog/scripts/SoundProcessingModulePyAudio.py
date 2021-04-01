#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wave
import time
import numpy as np
from os import path

import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from mbot_nlu.msg import ActionSlotArray
from sensor_msgs.msg import Image
from sensor_msgs.msg import PointCloud
from geometry_msgs.msg import Point32
from geometry_msgs.msg import Point

import cv2, random, time, base64
from cv_bridge import CvBridge, CvBridgeError

import imutils
import socket
import json
import speech_recognition as sr


class SoundProcessingModule(object):
	def __init__(self):
		super(SoundProcessingModule, self).__init__()
		print("connected")
		self.bridge = CvBridge()

		self.module_name = "SoundProcessingModule"

		self.dialog_type = ""
		node = rospy.init_node('InteractionModule')

		self.dialog_topic = ""

		self.drinks = ["beer", "chocolate milk", "coke", "lemonade", "tea", "water"]
		self.memory = []

		self.pub_turn = rospy.Publisher("cmd_vel", Twist,queue_size=10)
		self.count = 0
		self.server_ip = rospy.get_param('~server_ip','127.0.0.1')	 
		self.server_port = rospy.get_param('~server_port', 9987)
		self.server_ip_intents = rospy.get_param('~server_ip_intents','127.0.0.1')	 
		self.server_port_intents = rospy.get_param('~server_port_intents', 9986)

	def main(self):
		r = sr.Recognizer()

		with sr.Microphone() as source:
			r.adjust_for_ambient_noise(source) 
			print("Say something!")
			audio = r.listen(source)
			transcript = r.recognize_google(audio)
			print("Recognize: "+transcript)
			self.sample_recognize(transcript)

	def sample_recognize(self, response):
		if len(response) == 0:
			print("Can't understand")
		else:
			result = self.socket_request_sentence_analysis(response)
			print("Main topic: "+result["main_topic"])
			print("Category: "+result["category"])
			print("Sentiment: "+result["sentiment"])
			new_sentence = result["sentence"]

			#Scenario 1
			# if self.count < 3:
			#self.interaction2(result, new_sentence)

			#Scenario 2
			intents = self.socket_request(new_sentence)
			#self.technical_overview(intents, result)
			 

			self.dialog_topic = result["main_topic"]

			# if result["category"] == "Action-directive":
			# 	command = self.action_command(new_sentence)

			# 	for intent in command.sentence_recognition:
			# 		action = intent.intention
			# 		text += "I will try to perform the action "

			# 		text += action
			# 		for slot in intent.slots:
			# 			typ = slot.type
			# 			data = slot.data
			# 			text += "to the "
			# 			text += typ
			# 			text += data
			# 		self.alAnimatedSpeech.say(text,self.configuration)
				

			# # else:
			# # 	text = "I can't answer this type of question"
			# # 	self.alAnimatedSpeech.say(text,self.configuration)
			
			# duration = time.time() - timeStart
			# print("TOTAL ANSWER TIME: "+str(duration)+"s")

			# text = "I think your intention is "+intents["desire"]+"."
			# text += "Because I think you are "+intents["relation"]

			# self.alAnimatedSpeech.say(text,self.configuration)
			# text = "To do it you need "+intents["needs"]
			# self.alAnimatedSpeech.say(text,self.configuration)

			
			#list_responses = ["Of course", "OK, I'm on it.", "I'm on my way!"]

			# for drink in self.drinks:
			# 	if drink in str(self.dialog_topic):
			# 		text = random.choice(list_responses)
			# 		text += " I'll bring you "+self.dialog_topic
			# 		break
			# 	else:
			# 		text = "Sorry, I don't have "+self.dialog_topic
		
			# file = open("search_result.txt", "r")
			# content = file.read()
			# text = content
			# self.alAnimatedSpeech.say(text,self.configuration)
			# file.close()

	def recognize_google(self, local_file_path):
		r = sr.Recognizer()
		with sr.AudioFile(local_file_path) as source:
			audio = r.record(source) 
		try:

			transcription = r.recognize_google(audio)
			result = self.socket_request_sentence_analysis(transcription)
			print("Main topic: "+result["main_topic"])
			print("Category: "+result["category"])
			print("Sentiment: "+result["sentiment"])
			new_sentence = result["sentence"]

			#Scenario 2
			intents = self.socket_request(new_sentence)
			self.technical_overview(intents, result)
			 

			self.dialog_topic = result["main_topic"]

		except sr.UnknownValueError:
			print("Can't understand")
		except sr.RequestError as e:
			print("Could not request results from Google Speech Recognition service; {0}".format(e))

	def interaction1(self, features, new_sentence): 
		if self.dialog_topic == "":
			intents = self.socket_request(new_sentence)
			text = "I feel you are "+intents["relation"]+", do you want something "+intents["desire"]+" ?"
			self.alAnimatedSpeech.say(text,self.configuration)
			self.memory.append(new_sentence)
		else:
			text = "Ok, I'm on my way!"

			self.memory.append(new_sentence)

			for sentence in self.memory:

				command = self.action_command(sentence)

				for intent in command.sentence_recognition:
					action = intent.intention
					text += "I will perform the action "

					text += action
					for slot in intent.slots:
						typ = slot.type
						data = slot.data
						text += "to the "
						text += typ
						text += data
				text += ". And then "
			self.alAnimatedSpeech.say(text,self.configuration)
		

	def interaction2(self, features, new_sentence): 
		if self.dialog_topic == "":
			intents = self.socket_request(new_sentence)
			text = "Because you are "+intents["relation"]+", do you want something "+intents["desire"]+" ?"
			self.alAnimatedSpeech.say(text,self.configuration)
			self.memory.append(new_sentence)
		else:
			text = "Ok, follow me to the bar."
			
			self.alAnimatedSpeech.say(text,self.configuration)
			time.sleep(1)

			self.alMotion.moveTo(0.0,0.0,-3.1415)
			self.alMotion.moveTo(2.0,0.0,0.0)


	def technical_overview(self, intents, features):
		text = "The category of this question is "+features["category"]
		self.alAnimatedSpeech.say(text,self.configuration)

		text = "The main topic is "+features["main_topic"]
		self.alAnimatedSpeech.say(text,self.configuration)

		text = "The sentiment is mainly "+features["sentiment"]
		self.alAnimatedSpeech.say(text,self.configuration)

		for x in intents:
			if intents[x] == "none":
				intents[x] = "nothing"

		text = "I view the user as "+intents["relation"]
		self.alAnimatedSpeech.say(text,self.configuration)

		text = "The user intents is "+intents["intends"]
		self.alAnimatedSpeech.say(text,self.configuration)

		text = "The user may wants "+intents["desire"]
		self.alAnimatedSpeech.say(text,self.configuration)

		# text = "The user expect me "+intents["needs"]
		# self.alAnimatedSpeech.say(text,self.configuration)

		text = "I believe the user command is used for "+intents["utility"]
		self.alAnimatedSpeech.say(text,self.configuration)

		# text = "I believe the command is "+intents["type"]
		# self.alAnimatedSpeech.say(text,self.configuration)

		command = self.action_command(features["sentence"])

		if features["category"] == "Action-directive":
			text = "As an Action-directive command "
			for intent in command.sentence_recognition:
				action = intent.intention
				text += "I will perform the action "

				text += action
				for slot in intent.slots:
					typ = slot.type
					data = slot.data
					text += "to the "
					text += typ
					text += data
			self.alAnimatedSpeech.say(text,self.configuration)
			


	def detect_object(self, obj):
		msg=rospy.wait_for_message("/naoqi_driver/camera/front/image_raw", Image) 

		imageF = self.bridge.imgmsg_to_cv2(msg, "bgr8")

		#Resizing the image 
		imageF = imutils.resize(imageF, width=min(320, imageF.shape[1]))
		req = ServerRequestVis()
		output = req.request(imageF, "allDetection")

		class_names = ['person', 'bicycle', 'car', 'motorcycle', 'airplane',
			   'bus', 'train', 'truck', 'boat', 'traffic light',
			   'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird',
			   'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
			   'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
			   'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
			   'kite', 'baseball bat', 'baseball glove', 'skateboard',
			   'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
			   'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
			   'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
			   'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
			   'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
			   'keyboard', 'cell phone', 'microwave', 'oven', 'toaster',
			   'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors',
			   'teddy bear', 'hair drier', 'toothbrush']

		objects_detected = []
		print(output)
		for feature in output["ids"]:
			objects_detected.append(class_names[feature])
		print(objects_detected)
		print("Object "+str(obj))

		for objec in objects_detected:
			if objec == obj:
				return True
		return False



	def general_question_answering(self, question):
		seconds = time.time()

		req = ServerRequestNLP()
		output = req.request(question)
		
		duration = time.time() - seconds
		print("Question request duration : ")
		print(duration)
		print(output)
		print("------------")
		print(output["answer"])
		return output["answer"], output["topic"]

	def topic_extract(self, question):
		seconds = time.time()

		req = ServerRequestNLP()
		output = req.request(question)
		
		duration = time.time() - seconds
		# print("Question request duration : ")
		# print(duration)
		return output["topic"]

	def sentence_analysis(self, question):
		seconds = time.time()

		req = ServerRequestNLP()
		output = req.request(question)
		
		duration = time.time() - seconds
		# print("Question request duration : ")
		# print(duration)
		return output

	def intents_analysis(self, sentence):
		seconds = time.time()

		req = ServerRequestIntents()
		output = req.request(sentence)
		
		duration = time.time() - seconds
		# print("Question request duration : ")
		# print(duration)
		return output

	def socket_request(self, sentence):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((self.server_ip_intents, self.server_port_intents))
		print("Request commonsense intents . . . \n")
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


if __name__ == "__main__":
	process = SoundProcessingModule()
	process.main()