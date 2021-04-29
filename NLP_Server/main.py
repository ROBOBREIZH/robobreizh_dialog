from topic_extraction import Extractor
from NLPModule import NLPModule
import argparse

import socket
import json

def main():
	test = Extractor()
	nlp = NLPModule()

	question = input("Enter a question, tape 'end' to finish \n")

	while not question == "end":
		main_topic, sentence = test.extract(str(question))
		category = nlp.find_category(question)
		sentiment = nlp.sentiment_analysis(question)
		
		question = input("Enter a question, tape 'end' to finish \n")


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Launch the sentence analysis server.')
	parser.add_argument("--server_ip", type=str, default="127.0.0.1", help="Server IP address. Default localhost '127.0.0.1'.")	
	parser.add_argument("--server_port", type=int, default=9987, help="Server port address. Default '9987'.")	

	args = parser.parse_args()

	test = Extractor()
	nlp = NLPModule()
	socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket.bind((args.server_ip, args.server_port))
	print("Listening")
	main_topic = ""

	while True:
		socket.listen(1)
		client, address = socket.accept()
		print("{} connected".format(address))

		response = client.recv(9999999)
		if response != "":
				print(response)
		response = response.decode()

		main_topic, sentence = test.extract(str(response))
		category = nlp.find_category(response)
		sentiment = nlp.sentiment_analysis(response)

		result = {"main_topic": main_topic,
			"sentence": sentence,
			"category": category,
			"sentiment": sentiment}

		res_bytes = json.dumps(result).encode('utf-8') 

		client.send(res_bytes)
		
	print("Close")
	client.close()
	stock.close()

