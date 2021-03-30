import wave
import time
from naoqi import ALProxy
import soundfile as sf
import numpy as np
from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
import io
import qi
from Queue import Queue
#from NLPModule import NaturalLanguageProcessing
import execnet
import subprocess
import rospy
from std_msgs.msg import String
from mbot_nlu.msg import ActionSlotArray
from server_request_nlp import ServerRequestNLP
from server_request_vision import ServerRequestVis

import cv2, random, time, base64, numpy as np
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
from sensor_msgs.msg import PointCloud
from geometry_msgs.msg import Point32
from geometry_msgs.msg import Point
import shutil
import imutils
import math
from server_request_vision import ServerRequestVis

GOOGLE_APPLICATION_CREDENTIALS="/home/master/Documents/robocupHome/robocup-239813-9500eff38dda.json"
micData = []

class SoundProcessingModule(object):
	def __init__(self, app, stop_recognition):
		super(SoundProcessingModule, self).__init__()
		app.start()
		session = app.session	
		print("connected")
		self.bridge = CvBridge()

		self.alTextToSpeech = session.service("ALTextToSpeech")
		self.alTextToSpeech.setParameter("volume",100)
		self.alTextToSpeech.setParameter("pitch",100)
		self.alTextToSpeech.setParameter("speed",80)

		self.audio_service = session.service("ALAudioDevice")
		self.alDialog = session.service("ALDialog")
		self.alDialog.setLanguage("English")
		self.alAnimatedSpeech = session.service("ALAnimatedSpeech")
		self.configuration = {"bodyLanguageMode":"contextual"}
	
		self.audio_service.enableEnergyComputation()

		self.framesCount=0
		self.recordingInProgress = False
		self.stopRecognition = stop_recognition
		self.previous_sound_data = Queue(5)

		self.rstCounterSpeech = 2
		self.rstCounterSilence = 10
		self.setthOffset = 150.0
		self.setcounterSpeech = 2
		self.setcounterSil = 10
		self.setaval = 0.8
		self.timeOutInternalCounter =  140;
		self.rstTimeOutInternalCounter = 140;
		self.ymin_prev = 0
		self.ymax_prev = 0
		self.ymed_prev = 0
		self.ener_prev = 0
		self.thOffset = self.setthOffset
		self.counterSpeech = self.setcounterSpeech = self.rstCounterSpeech
		self.counterSilence = self.setcounterSil = self.rstCounterSilence
		self.status = "Silence"
		self.inSpeech = 0
		self.threshold = 0
		self.a = self.setaval 
		self.a1 = 1 - self.a
		self.firstTime = 1
		self.micData = []
		self.sound_data = []

		self.module_name = "SoundProcessingModule"

		self.dialog_type = ""
		node = rospy.init_node('InteractionModule')

		self.dialog_topic = ""

	def call_python_version(self, Version, Module, Function, ArgumentList):
		gw      = execnet.makegateway("popen//python=python%s" % Version)
		channel = gw.remote_exec("""
			from %s import %s as the_function
			channel.send(the_function(*channel.receive()))
		""" % (Module, Function))
		channel.send(ArgumentList)
		return channel.receive()

	def startProcessing(self):
		"""init sound processing, set microphone and stream rate"""
		print("startProcessing")

		if self.dialog_type == "":
			text = "Welcome, ask me anything"
			#text = "Please choose a type of dialog : General Question Answering or Action Commands"
			self.alTextToSpeech.say(text)
		self.audio_service.setClientPreferences(self.module_name, 16000, 3, 0)
		self.audio_service.subscribe(self.module_name)    
		while not self.stopRecognition.is_set():
			time.sleep(1)

		self.audio_service.unsubscribe(self.getName())

	def convertStr2SignedInt(self, data):
		signedData = []
		ind = 0
		for i in range(0, len(data)/2):
			signedData.append(data[ind]+data[ind+1]*256)

			ind = ind+2

		for i in range(0, len(signedData)):
			if signedData[i] >= 32768:
				signedData[i] = signedData[i]-65536

		for i in range(0, len(signedData)):
			signedData[i] = signedData[i]/32767.0

		return signedData

	def processRemote(self, nbOfChannels, nbOfSamplesByChannel, timeStamp, inputBuffer):
		"""audio stream callback method with simple silence detection"""
		self.sound_data = self.convertStr2SignedInt(inputBuffer)
		

		self.energy = (((self.audio_service.getFrontMicEnergy()*1.5) 
		+ (self.audio_service.getLeftMicEnergy()*1) 
		+ (self.audio_service.getRightMicEnergy()*1) 
		+ (self.audio_service.getRearMicEnergy()*0.5)) 
		/ 4)

		if (self.firstTime):
			self.ymin_prev = self.energy
			self.ymax_prev = self.energy
			self.ymed_prev = self.energy
			self.ener_prev = self.energy
			self.firstTime = 0

		if (self.energy > self.ymax_prev):
			self.ymax = self.energy
		else :
			self.ymax = self.a*self.ymax_prev + self.a1*self.ymed_prev
		if (self.energy < self.ymin_prev):
			self.ymin = self.energy
		else:
			self.ymin = self.a*self.ymin_prev + self.a1*self.ymed_prev
		self.ymed = (self.ymin+self.ymax)/2

		if (self.status == "Silence"):
			if (self.energy > self.ymed_prev + self.thOffset):
				self.status = "possibleSpeech"
				self.threshold = self.ymed_prev + self.thOffset
				self.counterSpeech = self.rstCounterSpeech - 1

		elif (self.status == "possibleSpeech"):
			self.counterSpeech = self.counterSpeech - 1
			if (self.energy > self.threshold and self.energy > self.ymed):
				if (self.counterSpeech  <= 0):
					self.counterSpeech = self.rstCounterSpeech
					self.status = "Speech" 
					self.startRecording()
					self.timeOutInternalCounter = self.rstTimeOutInternalCounter-self.rstCounterSpeech
				else:
					self.status = "possibleSpeech"

			else:
				self.status = "Silence"


		elif (self.status == "Speech"):
			if (self.energy < self.ymed):
				self.status = "possibleSilence"  
				self.threshold = self.ymed 
				self.counterSilence = self.rstCounterSilence-1

			else:
				self.status = "Speech"


		elif (self.status == "possibleSilence"):
			self.counterSilence = self.counterSilence - 1
			if (self.energy > self.ymed):
				self.status = "Speech"
				self.counterSilence = self.rstCounterSilence - 1

		
			if (self.counterSilence == 0):
				self.status = "Silence"
				self.stopRecording()
			else: 
				self.status = "possibleSilence"

		else:
			self.status = "Silence"


		if(self.status != "Silence"):
			self.timeOutInternalCounter = self.timeOutInternalCounter-1


		if(self.timeOutInternalCounter == 0):
			self.status = "Silence"
			self.timeOutInternalCounter = self.rstTimeOutInternalCounter
			print("SPEECH IS TAKING MORE TIME THAN EXPECTED.")

		self.ymin_prev = self.ymin
		self.ymax_prev = self.ymax
		self.ymed_prev = self.ymed
		self.ener_prev = self.energy
	

		if self.recordingInProgress:
		# 	self.previous_sound_data = self.sound_data
		# 	self.procssingQueue.put(self.sound_data)
			self.micData += self.sound_data
		else:
			if self.previous_sound_data.full():
				self.previous_sound_data.get()

			self.previous_sound_data.put(self.sound_data)
		#print(self.status)


	def startRecording(self):
		"""init a in memory file object and save the last raw sound buffer to it."""
		#self.procssingQueue = Queue()
		self.recordingInProgress = True    
		#if not previous_sound_data is None:
			#self.procssingQueue.put(previous_sound_data)
		while not self.previous_sound_data.empty():
			self.micData += self.previous_sound_data.get()

		print("start recording")


	def stopRecording(self):
		"""saves the recording to memory"""
		print("stopped recording")

		filename = "/home/master/stereo_file.wav"

		sf.write(filename, self.micData, 16000, 'PCM_16')
		self.recordingInProgress = False
		self.micData = []
		self.sample_recognize(filename)


	def sample_recognize(self, local_file_path):
		"""
		Transcribe a short audio file using synchronous speech recognition

		Args:
		  local_file_path Path to local audio file, e.g. /path/audio.wav
		"""

		client = speech_v1.SpeechClient()

		# local_file_path = 'resources/brooklyn_bridge.raw'

		# The language of the supplied audio
		language_code = "en-US"

		# Sample rate in Hertz of the audio data sent
		sample_rate_hertz = 16000

		# Encoding of audio data sent. This sample sets this explicitly.
		# This field is optional for FLAC and WAV audio formats.
		config = {
			"language_code": language_code,
			"sample_rate_hertz": sample_rate_hertz,
		}

		with io.open(local_file_path, "rb") as f:
			content = f.read()
		audio = {"content": content}

		response = client.recognize(config, audio)

		if len(response.results) == 0:
			print("Can't understand")
		else:
			for result in response.results:
				print(u'Transcript: {}'.format(result.alternatives[0].transcript))
				print(u'Confidence: {}'.format(result.alternatives[0].confidence))

				transcription = result.alternatives[0].transcript
				print(transcription)


				self.dialog_topic, sentence = self.topic_extract(transcription)

				list_responses = ["Of course, I'll bring you one.", "OK, I'm on it.", "I'm on my way!"]

				for drink in self.drinks:
					if drink in self.dialog_topic:
						text = random.choice(list_responses)
					else:
						text = "Sorry, I don't have this drink"
					self.alAnimatedSpeech.say(text,self.configuration)


				self.dialog_type = "AC"
				if self.dialog_type == "QA":
					text = "I will try to find the answer to the question : "
					text += transcription
					self.alAnimatedSpeech.say(text,self.configuration)
					text = "Please wait this may take a while"
					self.alAnimatedSpeech.say(text,self.configuration)
					answer, topic = self.general_question_answering(transcription)

					self.alAnimatedSpeech.say(answer,self.configuration)
					self.dialog_topic = topic


				elif self.dialog_type == "AC":
					text = ""
					features = []
					command = self.action_command(transcription)

					for intent in command.sentence_recognition:
						text = "I will perform the action "

						action = intent.intention
						if action == "tell":
							print("test")

							for slot in intent.slots:
								typ = slot.type
								data = slot.data
								
								if "my age" in data:
									features = self.wait_for_person()
									break

						text += action
						for slot in intent.slots:
							typ = slot.type
							data = slot.data
							text += " to the "
							text += typ
							text += " "
							text += data
							if typ == "object":
								if self.detect_object(data):
									text2 = "I see the object "+data+" in the room"
								else:
									text2 = "I don't see the object "+data+" in the room"
								print(text2)
								self.alTextToSpeech.say(text2)


						#print(text)
						#self.alAnimatedSpeech.say(text,self.configuration)



					if(len(features)!=0):
						text = "For sure. You are about "
						text += features.age
						text += " years old"




				qa_list = ['general question', 'general questions', 'generals question', 'question answer', 'questions answer', 'question answering', 'questions answering', 'question', 'questions', 'answering']
				ac_list = ['action commands', 'action command', 'command', 'commands']

				if  'question' in transcription or 'answer' in transcription:
					self.dialog_type = "QA"
					text = "I will only answer general questions from now"
					self.alAnimatedSpeech.say(text,self.configuration)

				elif 'action' in transcription or 'command' in transcription:
					self.dialog_type = "AC"
					text = "I will only execute action commands from now"
					self.alAnimatedSpeech.say(text,self.configuration)

				if self.dialog_type == "":
					text = "Sorry I didn't understand. Please choose a type of dialog : General Question Answering or Action Commands."
					self.alAnimatedSpeech.say(text,self.configuration)

			
				# file = open("search_result.txt", "r")
				# content = file.read()
				# text = content
				# self.alAnimatedSpeech.say(text,self.configuration)
				# file.close()

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
		print(output["answer"])
		return output["answer"], output["topic"]


	def action_command(self, command):
		seconds = time.time()
		self.pub = rospy.Publisher('hri/nlu/mbot_nlu/input_sentence', String,  queue_size=10)
		rospy.sleep(1)
		self.pub.publish(command)

		msg = rospy.wait_for_message('hri/nlu/mbot_nlu/output_recognition', ActionSlotArray) 

		duration = time.time() - seconds
		print("Command request duration : ")
		print(duration)

		return msg


	def wait_for_person(self):
		t = time.time()
		trouve = False 
		j = 0
		while True:
			features = self.personDetect()
			currentTime = time.time() - t

			bool_face = True
			bool_age = True
			bool_clothes = True

			if "NONE" in features:
				bool_face = False
			if 0 in features:
				bool_age = False
			if ["NONE", "NONE"] in features:
				bool_clothes = False

			if currentTime >= 15.0:
				bool_face = True
				bool_age = True
				bool_clothes = True

			if  bool_face and bool_age and bool_clothes:
				trouve = True

				tab.age = features[0*2]
				tab.gender = features[0*2+1]
				tab.clothes = features[0*2+2]
				print("age person : "+str(features[0*2]))
				print("gender person : "+str(features[0*2+1]))
				print("clothes person : "+str(features[0*2+2]))
				
				break

		return tab

	def personDetect(self):
		print("test 4")
		msg=rospy.wait_for_message("/naoqi_driver/camera/front/image_raw", Image) 

		imageF = self.bridge.imgmsg_to_cv2(msg, "bgr8")

		#Resizing the image 
		imageF = imutils.resize(imageF, width=min(320, imageF.shape[1]))

		#time.sleep(2.0)
		req = ServerRequestVis()
		output = req.request(imageF, "personDetect")

		#Calcul HFOV et VFOV
		features = []

		personNum = 0
		for tab in output["isPerson"]:

			if len(output["features"]) == 0:
				features.append(0)
				features.append("NONE")
				features.append(["NONE","NONE"])
			i = 0
			
			for i in range(len(output["features"])):
				#bounding_box = output["features"][i][0]
				#if self.intersecting(bounding_box, [xmin, ymin, xmax, ymax]):
				age = output["features"][i][1]
				gender  = output["features"][i][2]
				clothes = output["features"][i][3]
				
				features.append(age)
				features.append(gender)
				for j in range(2):
					if (clothes[j] == ""):
						clothes[j] = "NONE"
				features.append(clothes)
				# else:
				# 	features.append(0)
				# 	features.append("NONE")
				# 	features.append(["NONE", "NONE"])

		return features