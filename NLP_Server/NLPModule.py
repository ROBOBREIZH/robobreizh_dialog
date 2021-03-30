#!/usr/bin/env python3.7

from transformers import pipeline
import sys
import spacy
import time
#import torch
# from transformers import AutoTokenizer, AutoModelForQuestionAnswering
# from transformers import BertForQuestionAnswering
# from transformers import BertTokenizer
# from transformers import GPT2Tokenizer, GPT2LMHeadModel
#from transformers import pipeline
#from src.nlp.Question_Classification.classify_questions import classify_question
import logging
import pprint as pp

import wikipedia
#import matplotlib.pyplot as plt
#import seaborn as sns
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from topic_extraction import Extractor

from DialogTag.dialog_tag.DialogTag import DialogTag


class NLPModule(object):
	"""docstring for NLPModule"""		
			
	def answer_question2(self, sentence):
		seconds = time.time()

		topic, nouns, verbs = self.spacy_extract(sentence)
		if(topic == "Extraction issue"):
			return "NLP error", ""

		duration = time.time() - seconds
		print("############## Extract entities duration : ")
		print(duration)

		seconds = time.time()

		try:
			results = wikipedia.search(sentence)
			print("Wikipedia search results for our question:\n")
			pp.pprint(results)
		except wikipedia.exceptions.DisambiguationError as e:
			print(e)
		except wikipedia.exceptions.PageError as e:
			print(e)
		except wikipedia.exceptions.HTTPTimeoutError as e:
			print(e)


		trouve = 0

		if(len(results) != 0):
			wiki_page = results[0]
			for res in results:
				if (res == topic):
					trouve = 1
					wiki_page = res
					break

		if trouve == 0:
			results = wikipedia.search(topic)
			print("Wikipedia search from extracted topic :\n")
			pp.pprint(results)
			if(len(results) != 0):
				wiki_page = results[0]
			else:
				return "Sorry, I couldn't find any wikipedia result for your question", ""

		print("Wikipedia page :")
		print(wikipedia.page(wiki_page).title)
		context = wikipedia.summary(wiki_page, sentences=10)

		#context = wikipedia.page(results[0]).content
		duration = time.time() - seconds
		print("################## Get wikipedia duration : ")
		print(duration)

		question = sentence

		seconds = time.time()

		model_name = "bert-large-cased-whole-word-masking-finetuned-squad"
		nlp_qa = pipeline("question-answering", 
						  model=model_name, 
						  tokenizer=model_name,
						  framework="pt")

		result = nlp_qa(question=question, context=context)
		answer = result["answer"]
		score = result["score"]

		print("")
		print("Question: {}".format(question))
		print("Answer: {}".format(answer))
		print("Score: {}".format(score))
		duration = time.time() - seconds
		print("################## Get answer duration : ")
		print(duration)

		return self.answer_generation(sentence, answer), topic

	def visualize_score(self, start_scores, end_scores, tokens):
		# Use plot styling from seaborn.
		sns.set(style='darkgrid')

		# Increase the plot size and font size.
		#sns.set(font_scale=1.5)
		plt.rcParams["figure.figsize"] = (16,8)

		# Pull the scores out of PyTorch Tensors and convert them to 1D numpy arrays.
		s_scores = start_scores.detach().numpy().flatten()
		e_scores = end_scores.detach().numpy().flatten()

		# We'll use the tokens as the x-axis labels. In order to do that, they all need
		# to be unique, so we'll add the token index to the end of each one.
		token_labels = []
		for (i, token) in enumerate(tokens):
			token_labels.append('{:} - {:>2}'.format(token, i))


		# Create a barplot showing the start word score for all of the tokens.
		ax = sns.barplot(x=token_labels, y=s_scores, ci=None)

		# Turn the xlabels vertical.
		ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha="center")

		# Turn on the vertical grid to help align words to scores.
		ax.grid(True)

		plt.title('Start Word Scores')

		plt.show()

	def answer_generation(self, question, answer):
		'''

		#NLG test with GPT-2

		seconds = time.time()

		# Load pre-trained model tokenizer (vocabulary)
		tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

		# Encode a text inputs
		text = nouns + " "+ verbs +" "+ ent +" "+ answer 
		indexed_tokens = tokenizer.encode(text)

		# Convert indexed tokens in a PyTorch tensor
		tokens_tensor = torch.tensor([indexed_tokens])


		# Load pre-trained model (weights)
		model = GPT2LMHeadModel.from_pretrained('gpt2')

		# Set the model in evaluation mode to deactivate the DropOut modules
		# This is IMPORTANT to have reproducible results during evaluation!
		model.eval()

		# If you have a GPU, put everything on cuda
		tokens_tensor = tokens_tensor.to('cuda')
		model.to('cuda')

		# Predict all tokens
		with torch.no_grad():
			outputs = model(tokens_tensor)
			predictions = outputs[0]

		# get the predicted next sub-word (in our case, the word 'man')
		predicted_index = torch.argmax(predictions[0, -1, :]).item()
		predicted_text = tokenizer.decode(indexed_tokens + [predicted_index])

		print("Predicted answer : "+predicted_text)

		duration = time.time() - seconds
		print("################## Predicted answer duration : ")
		print(duration)
		'''
		answer = "According to Wikipedia the answer to your question is : " + answer

		return answer


	def sentiment_analysis(self, sentence):
		sid = SentimentIntensityAnalyzer()
		print(sentence)
		ss = sid.polarity_scores(sentence)
		if ss["neg"] >= 0.5:
			print("sentiment negative")
			return "negative"
		if ss["pos"] >= 0.5:
			print("sentiment positive")
			return "positive"
		if ss["neu"] >= 0.5:
			print("sentiment neutral")
			return "neutral"
			
	def find_category(self, sentence):
		''' We define three different question categories: 
		- General question answering: Knowledge - base questions
		- Contextual requests: action commands with interaction into the world
		- General speech: general interaction about names, feelings etc... 
		
		This goal of this method is to get the category of the interaction
		'''
		model = DialogTag('distilbert-base-uncased')
		prediction = model.predict_tag(sentence)
		print("Predicted category: "+prediction)
		return prediction

if __name__ == "__main__":

	print(str(sys.argv[1]))
	test = NLPModule()
	res = test.answer_question2(str(sys.argv[1]))
	print(res)