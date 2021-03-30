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
import getpass
micData = []

class SoundProcessingModule(object):
	def __init__(self, app, stop_recognition):
		super(SoundProcessingModule, self).__init__()
		app.start()
		session = app.session	
		print("connected")

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
		self.previous_sound_data = None

		self.rstCounterSpeech = 2
		self.rstCounterSilence = 10
		self.setthOffset = 200.0
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
		print(self.module_name)
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
					self.startRecording(self.previous_sound_data)
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
			self.previous_sound_data = self.sound_data
			self.procssingQueue.put(self.sound_data)
			self.micData += self.sound_data

		#print(self.status)


	def startRecording(self, previous_sound_data):
		"""init a in memory file object and save the last raw sound buffer to it."""
		self.procssingQueue = Queue()
		self.recordingInProgress = True    
		if not previous_sound_data is None:
			self.procssingQueue.put(previous_sound_data)
			self.micData += previous_sound_data

		print("start recording")


	def stopRecording(self):
		"""saves the recording to memory"""
		print("stopped recording")
		self.previous_sound_data = None
		username = getpass.getuser()

		filename = "/home/"+username+"/stereo_file.wav"

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

				arg1 = "\""+result.alternatives[0].transcript+"\""
				print(arg1)
				#exit_code = call("python3 NLPModule.py " + arg1, shell=True)

				text = "I will try to find the answer to the question : "
				text += arg1
				self.alAnimatedSpeech.say(text,self.configuration)

				seconds = time.time()

				proc = subprocess.Popen(['python3', 'NLPModule.py',  arg1], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
				ans = proc.communicate()[0]
				print(ans)
				duration = time.time() - seconds
				print("request duration : ")
				print(duration)
				file = open("search_result.txt", "r")
				content = file.read()
				text = content
				self.alAnimatedSpeech.say(text,self.configuration)
				file.close()
			  


			
