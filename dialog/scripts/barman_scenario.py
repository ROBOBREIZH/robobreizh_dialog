from naoqi import ALProxy
import soundfile as sf

'''
POUR MAEL ET SANDRA :
Modifier les deux lignes suivantes avec la nouvelle API
'''
from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
import io
import qi
from Queue import Queue
from NLPModule import NLPModule
import execnet
import rospy
from std_msgs.msg import String
#from mbot_nlu.msg import ActionSlotArray
from server_request_nlp import ServerRequestNLP
from server_request_vision import ServerRequestVis

import cv2, random, time, base64, numpy as np
# from sensor_msgs.msg import Image
# from sensor_msgs.msg import PointCloud
# from geometry_msgs.msg import Point32
# from geometry_msgs.msg import Point
# import imutils

import random
from topic_extraction import Extractor
''' 
Path tp the Google API credentials, see 
https://cloud.google.com/speech-to-text/docs/quickstart-client-libraries
for more info
'''

# GOOGLE_APPLICATION_CREDENTIALS="/home/master/Documents/robocupHome/robocup-239813-9500eff38dda.json"

# Internal buffer that store only the data that should be send to Google
micData = []

'''

This Module provid a speech recognition algorithm and a ersatz of interaction module

The processing pipeline is as follow:
1. We connect to Naoqi Audio API
2. We retrieve all sound data from 4 microphones via a callback method processRemote()
	- Example of the structure used from Naoqi tutorial:
	http://doc.aldebaran.com/2-4/dev/python/examples/audio/audio_soundprocessing.html
3. Those data feed an internal buffer inputBuffer
4. We access the intensity of each microphones via the API (getLeftMicEnergy, getRightMicEnergy etc...) and compute a global intensity value (self.energy)
5. This value is used in the a State Machine to decide if someone is possibly talking 
6. The State Machine is build upon 4 different states as follow:
	- Silence: initialize with the original sound average value (normalize)
	- Possible Speech: if the original value reach a threshold (a % of higher volume from the Silence value) we switch state here
	- Speech: if Possible Speech as been trigger for a certain number of chunk then it become Speech state
	- PossibleSilence: if it's in Speech state and the value decrease from a certain % then the Machine state here
	- Silence: if we are in PossibleSilence for a certain number of chunk then we come back to silence, updating the average value (corresponding to the ambiant noise)
7. If state Speech is triggered the Speech Recognition start by sending the audio data to Google via the Google STT API
8. We retrieve the transcription from Google and send it to the Q&A Module for general question answering or to the action detection node (currently Mbot ROS implementation)

The goal of this pipeline is to limit the recognition requests to Google when it's not necessary. 
Ex: when there is a short sound like door closing the module should not detect it as a voice input.

TODO: improve the detection by 2 steps:
	- increasing the time to transit from PossibleSpeech to Speech, this need to increase the pre-buffer (temporary buffer that store data not recorded when the recognition start)
	- analyze the audio feed to detect human voice freqquency

Note: All values for the internal variables of the module had been set experimentaly and should be tested.

'''

class SoundProcessingModule(object):
	def __init__(self, app, stop_recognition):
		super(SoundProcessingModule, self).__init__()
		app.start()
		session = app.session	
		print("connected")

		self.alTextToSpeech = session.service("ALTextToSpeech")
		#self.alTextToSpeech.setParameter("volume",100)
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
		self.extractor = Extractor()
		file = open("Knowledge_base/drinks.txt","r")
		self.drinks = [line.rstrip('\n') for line in open(file)]

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
			text = "Hi, my name is Pepper and I am the new barman! What do you want to drink?"
			self.alAnimatedSpeech.say(text,self.configuration)
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

				self.dialog_topic = self.extractor.extract(transcription)
				list_responses = ["Of course, I'll bring you one.", "OK, I'm on it.", "I'm on my way!"]

				for drink in self.drinks:
					if drink in self.dialog_topic:
						text = random.choice(list_responses)
					else:
						text = "Sorry, I don't have this drink"
					self.alAnimatedSpeech.say(text,self.configuration)




			
				# file = open("search_result.txt", "r")
				# content = file.read()
				# text = content
				# self.alAnimatedSpeech.say(text,self.configuration)
				# file.close()
			  

	def general_question_answering(self, question):
		seconds = time.time()
		nlp = NLPModule()

		output, topic = nlp.answer_question2(str(question))
		
		duration = time.time() - seconds
		print("Question request duration : ")
		print(duration)
		print(output)
		print("------------")
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