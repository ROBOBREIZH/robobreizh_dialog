#!/usr/bin/env python
# -*- coding: utf-8 -*-
from socket import *

import threading
from SoundProcessingModule import SoundProcessingModule
import argparse
import time



def server():
	host = ""
	port = 13000

	buf = 1024
	addr = (host, port)
	host2 = "192.168.11.192"
	port2 = 9989

	addr2 = (host2, port2)

	UDPSock = socket(AF_INET, SOCK_DGRAM)

	UDPSock.bind(addr)
	print "Waiting to receive messages..."
	while True:
		(data, addr) = UDPSock.recvfrom(buf)
		print(addr)
		print "Received message: " + data
		data = "bien reçu"
		time.sleep(2)
		UDPSock2 = socket(AF_INET, SOCK_DGRAM)

		UDPSock2.sendto(data, addr2)
	UDPSock.close()
	os._exit(0)
	
if __name__ == '__main__':
	server()