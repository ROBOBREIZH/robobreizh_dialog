#!/usr/bin/env python3.6
from transformers import pipeline
import sys
import time
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from transformers import BertForQuestionAnswering
from transformers import BertTokenizer
import pprint as pp
from threading import Thread
import wikipedia
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from topic_extraction import Extractor
from DialogTag.dialog_tag.DialogTag import DialogTag
import spacy 

class NLPModule(object):
	"""docstring for NLPModule"""		
			
	def __init__(self):
		self.main_topic = ""
		self.current_topic = ""
		self.nlp = spacy.load("en_core_web_sm")
		self.sentence = ""
		self.extractor = Extractor()

	def answer_question2(self, sentence):
		self.sentence = sentence
		seconds = time.time()

		topic, nouns, verbs = self.spacy_extract(self.sentence)
		if(topic == "Extraction issue"):
			return "NLP error", ""

		duration = time.time() - seconds
		print("############## Extract entities duration : ")
		print(duration)

		seconds = time.time()

		try:
			page_topic = wikipedia.page(topic)
			print("Wikipedia page :")
			print(page_topic.title)
		except PageError:
			results = wikipedia.search(self.sentence)
			print("Wikipedia search results for our question:\n")
			pp.pprint(results)
			if(len(results) != 0):
				if (not(results[0] in topic) and not(topic in results[0])):
					results = wikipedia.search(topic)
				
			else:
				results = wikipedia.search(topic)

			print("Wikipedia search from extracted topic :\n")
			pp.pprint(results)

			print("Wikipedia page :")
			page_topic = wikipedia.page(results[0]).title

		context = wikipedia.summary(page_topic.title)
		#print(context)
		#context = wikipedia.page(page_topic).content
		duration = time.time() - seconds
		print("################## Get wikipedia duration : ")
		print(duration)

		question = self.sentence
		seconds = time.time()

		answer = self.question_answering(question, context)

		duration = time.time() - seconds
		print("################## Get answer duration : ")
		print(duration)
		
		return self.answer_generation(self.sentence, answer), topic

	def question_answering(self, question, context):
		tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-distilled-squad")

		model = AutoModelForQuestionAnswering.from_pretrained("distilbert-base-uncased-distilled-squad")
		
		nlp_qa = pipeline("question-answering")

		result = nlp_qa(question=question, context=context)
		answer = result["answer"]
		score = result["score"]

		print("")
		print("Question: {}".format(question))
		print("Answer: {}".format(answer))
		print("Score: {}".format(score))

		return answer

	def question_answering2(self, question, context):

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
		ss = sid.polarity_scores(sentence)
		if ss["neg"] >= 0.5:
			print("Sentiment: negative")
			return "negative"
		if ss["pos"] >= 0.5:
			print("Sentiment: positive")
			return "positive"
		if ss["neu"] >= 0.5:
			print("Sentiment: neutral")
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

	test = NLPModule()

	question = input("Enter a question, tape 'end' to finish \n")

	while not question == "end":
		res, test.topic = test.answer_question2(str(question))
		#print(res)
		question = input("Enter a question, tape 'end' to finish \n")

