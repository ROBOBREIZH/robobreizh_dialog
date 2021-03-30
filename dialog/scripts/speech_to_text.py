#!/usr/bin/env python
# -*- coding: utf-8 -*-
from std_msgs.msg import String, Float64MultiArray
import rospy
from naoqi import ALProxy
import qi
import threading
from SoundProcessingModule import SoundProcessingModule
import argparse


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
	stop_recognition = threading.Event()

	MySoundProcessingModule = SoundProcessingModule(app, stop_recognition)
	app.session.registerService("SoundProcessingModule", MySoundProcessingModule)
	MySoundProcessingModule.startProcessing()

	print("disconnected")

