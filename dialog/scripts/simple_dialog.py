#!/usr/bin/env python3.6
from naoqi import ALProxy

import sys
import spacy
import time

import pprint as pp
from threading import Thread
import wikipedia
#import matplotlib.pyplot as plt
#import seaborn as sns
from spacy import displacy
from nltk import Tree
from genderize import Genderize

class simple_dialog(object):
	"""docstring for NLPModule"""		
			
	def __init__(self):
		self.main_topic = ""
		self.current_topic = ""
		self.nlp = spacy.load("en_core_web_sm")
		self.sentence = ""



if __name__ == "__main__":

	test = NLPModule()

	question = input("Enter a question, tape 'end' to finish \n")

	while not question == "end":
		res, test.topic = test.answer_question2(str(question))
		#print(res)
		question = input("Enter a question, tape 'end' to finish \n")

