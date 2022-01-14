from naoqi import ALProxy
import numpy as np
import io
import qi
import rospy
import sys
from std_msgs.msg import String

if __name__ == "__main__":

	ip = sys.argv[1]
	port = 9559

	try:
	    # Initialize qi framework.
	    connection_url = "tcp://" + ip + ":" + str(port)
	    app = qi.Application(["SoundProcessingModule", "--qi-url=" + connection_url])
	except RuntimeError:
	    print ("Can't connect to Naoqi at ip \"" + ip + "\" on port " + str(port) +".\n"
	           "Please check your script arguments. Run with -h option for help.")
	    sys.exit(1)

	app.start()
	session = app.session	
	asr_service = session.service("ALAnimatedSpeech")
	alTextToSpeech = session.service("ALTextToSpeech")
	alTextToSpeech.setParameter("volume",120)
	alTextToSpeech.setParameter("pitch",110)
	alTextToSpeech.setParameter("speed",60)

	configuration = {"bodyLanguageMode":"contextual"}
	
	sentence = raw_input("Enter a sentence \n")
	
	while not sentence == "end":
		asr_service.say(sentence, configuration)
		sentence = raw_input("Enter a sentence \n")

	print("disconnected")


