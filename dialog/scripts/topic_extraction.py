import sys
import spacy
import time
from spacy import displacy
from nltk import Tree
from genderize import Genderize
#import explacy
import string
import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer
#from DialogTag.dialog_tag.DialogTag import DialogTag

from DialogTag.dialog_tag.DialogTag import DialogTag

# https://www.analyticsvidhya.com/blog/2020/06/nlp-project-information-extraction/

class Extractor(object):

	def __init__(self):
		self.main_topic = str()
		self.current_topic = str()
		self.sentence = str()
		self.nlp = spacy.load("en_core_web_sm")

	def extract(self, sentence):
		'''
		Two steps : 
			1. Trying to find a topic in the sentence
			2. If there is not, trying to deduce if a pronum can be related to the previous topic
			3. If not trying to deduce if a topic can be related to embeded world data
		''' 
		self.sentence = sentence
		self.current_topic = ""


		######### 1. #########
		#1.1. Parsing the sentence into tokens
		doc = self.nlp(self.sentence)
		self.spacy_visualize(doc, sentence)

		#1.2. Retrieve commun nouns and verbs
		nouns = []
		verbs = []

		for chunk in doc.noun_chunks:
			nouns.append(chunk.text)

		for possible_subject in doc:
			if possible_subject.dep == 'nsubj' and possible_subject.head.pos == 'VERB':
				verbs.append(possible_subject.head)
		
		#1.3. Find named entities, phrases and concepts from question type
		category = ""
		questions = ['how', 'when', 'who', 'what', 'where', 'which']
		if doc[0].lemma_ in questions:
			category = doc[0].lemma_
		
		entities = []
		list_entity = ['PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE', 'DATE']
		list_when = ['PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE']
		list_who = ['PERSON', 'NORP']

		# if category == "when":
		# 	self.current_topic = self.check_entity(doc, list_when)

		# if category == "who":
		# 	self.current_topic = self.check_entity(doc, list_who)
		# else :
		# 	self.current_topic = self.check_entity(doc, list_entity)

		#1.4 Extract topic, 8 possible solutions
		if self.current_topic =="":
			for token in doc:
				res = ""
				if(token.lemma_ not in questions):
					if(("nsubj" in token.dep_) and (token.text == "I")):
						for token in doc:
							if(("dobj" in token.dep_) and (token.pos_ == "NOUN")):
								self.current_topic = token.lemma_
								break

					# Handdle topics composed of commun nouns like : 'the first law of robotics'
					elif((("nsubj" in token.dep_) or (token.dep_ == "dobj") or (token.dep_ == "pobj")) and ((token.pos_ == "PRON") or (token.pos_ == "PROPN") or (token.pos_ == "NOUN"))):
						for t in token.subtree:
							res += t.text+" "
						self.current_topic = res.strip()
						break

			if self.current_topic == "":
				for token in doc:
					if("ROOT" in token.dep_):
						for t in token.subtree:
							res += t.text+" "
						self.current_topic = res.strip()
						break

		#1.5. Trying to replace actual pronum by the previous main topic
		done = False
		if (self.current_topic.upper() in map(str.upper, ["it", "he", "she", "him", "her"])) and (self.main_topic != ""):
			doc = self.nlp(self.main_topic)
			self.current_topic = self.current_topic.lower()
			for entity in doc.ents:
				if entity.label_ == "PERSON":
					gender = Genderize().get(self.main_topic)
					gender = gender[0]['gender']
					if ((gender == "male" and ((self.current_topic in ["him","he"]))) or (gender == "female" and ((self.current_topic in ["her","she"])))):	
						done = True
			
			if not done:
				if self.current_topic == "it":
					done = True

			if done:
				self.sentence = " "+self.sentence.translate(str.maketrans({key: " {0} ".format(key) for key in string.punctuation}))+" "
				src_str  = re.compile(" "+self.current_topic+" ", re.IGNORECASE)
				self.sentence  = src_str.sub(" "+self.main_topic+" ", self.sentence)
			else:
				print("Error replacing topic")

			self.current_topic = self.main_topic
		
		elif (self.main_topic != ""):
			for token in doc:
				if (token.text.upper() in map(str.upper, ["it", "he", "she", "him", "her"])):
					doc2 = self.nlp(self.main_topic)
					for entity in doc2.ents:
						if entity.label_ == "PERSON":
							gender = Genderize().get(self.main_topic)
							gender = gender[0]['gender']
							if ((gender == "male" and ((token.text.lower() in ["him","he"]))) or (gender == "female" and ((token.text.lower() in ["her","she"])))):	
								done = True
					
					if not done:
						if token.text.lower() == "it":
							done = True

					if done:
						self.sentence = " "+self.sentence.translate(str.maketrans({key: " {0} ".format(key) for key in string.punctuation}))+" "
						src_str  = re.compile(" "+token.text.lower()+" ", re.IGNORECASE)
						self.sentence  = src_str.sub(" "+self.main_topic+" ", self.sentence)
					else:
						print("Error replacing topic")

					self.current_topic = self.main_topic
					break
		
			# if current_topic == "":
			# 	if(len(nouns) == 1):
			# 		print("main topic entity")
			# 		self.current_topic  = nouns[0]
			# 		print(self.current_topic )
			# 	else:
			# 		return "Extraction issue", nouns, verbs

		self.current_topic = re.sub(r'\s([?.!,"](?:\s|$))', r'\1', self.current_topic)
		self.sentence = re.sub(r'\s([?.!,"](?:\s|$))', r'\1', self.sentence)

		print("New sentence:"+self.sentence)
		self.main_topic = self.current_topic
		self.main_topic = self.main_topic.translate(str.maketrans('', '', string.punctuation)).lower()
		print("Main topic : "+self.main_topic)
		#category = self.find_category(self.sentence)

		return self.main_topic, self.sentence

	def rule1(self, text):
    
	    doc = self.nlp(text)
	    
	    sent = []
	    
	    for token in doc:
	        
	        # if the token is a verb
	        if (token.pos_=='VERB'):
	            
	            phrase =''
	            
	            # only extract noun or pronoun subjects
	            for sub_tok in token.lefts:
	                
	                if (sub_tok.dep_ in ['nsubj','nsubjpass']) and (sub_tok.pos_ in ['NOUN','PROPN','PRON']):
	                    
	                    # add subject to the phrase
	                    phrase += sub_tok.text

	                    # save the root of the verb in phrase
	                    phrase += ' '+token.lemma_ 

	                    # check for noun or pronoun direct objects
	                    for sub_tok in token.rights:
	                        
	                        # save the object in the phrase
	                        if (sub_tok.dep_ in ['dobj']) and (sub_tok.pos_ in ['NOUN','PROPN']):
	                                    
	                            phrase += ' '+sub_tok.text
	                            sent.append(phrase)
	            
	    return sent


	def rule2(self, text): #Rule on adjective
    
	    doc = self.nlp(text)

	    pat = []
	    
	    # iterate over tokens
	    for token in doc:
	        phrase = ''
	        # if the word is a subject noun or an object noun
	        if (token.pos_ == 'NOUN')\
	            and (token.dep_ in ['dobj','pobj','nsubj','nsubjpass']):
	            
	            # iterate over the children nodes
	            for subtoken in token.children:
	                # if word is an adjective or has a compound dependency
	                if (subtoken.pos_ == 'ADJ') or (subtoken.dep_ == 'compound'):
	                    phrase += subtoken.text + ' '
	                    
	            if len(phrase)!=0:
	                phrase += token.text
	             
	        if  len(phrase)!=0:
	            pat.append(phrase)
	        
	    
	    return pat

	def rule3(self, text):
    
	    doc = self.nlp(text)
	    
	    sent = []
	    
	    for token in doc:

	        # look for prepositions
	        if token.pos_=='ADP':

	            phrase = ''
	            
	            # if its head word is a noun
	            if token.head.pos_=='NOUN':
	                
	                # append noun and preposition to phrase
	                phrase += token.head.text
	                phrase += ' '+token.text

	                # check the nodes to the right of the preposition
	                for right_tok in token.rights:
	                    # append if it is a noun or proper noun
	                    if (right_tok.pos_ in ['NOUN','PROPN']):
	                        phrase += ' '+right_tok.text
	                
	                if len(phrase)>2:
	                    sent.append(phrase)
	                
	    return sent

	def test_3_rules(self, sentence):
		print("Rule 1: ")
		print(self.rule1(sentence))

		print("Rule 2: ")
		print(self.rule2(sentence))

		print("Rule 3: ")
		print(self.rule3(sentence))


	def check_noun(self, entity, nouns):
		for n in nouns:
			return(n if entity in n else entity)

	def check_entity(self, doc, list_ent):
		entities=[]
		for entity in doc.ents:
			if(entity.label_ in list_ent):
				#print(entity)
				entities.append(entity.text)	
		if(len(entities) > 1): print("too much entities")	
		#TODO : handle multiple entities
		return(entities[0] if len(entities)>0 else "")


	def spacy_visualize(self, doc, sentence):
		#[self.to_nltk_tree(sent.root).pretty_print(unicodelines=True, nodedist=4) for sent in doc.sents]
		#explacy.print_parse_info(self.nlp, sentence)

		#[self.to_nltk_tree(sent.root).draw() for sent in doc.sents]
		#[self.to_nltk_tree_general(doc).draw() for sent in doc.sents]
		pass


	def to_nltk_tree(self, node):
		if node.n_lefts + node.n_rights > 0:
			return Tree(node.orth_, [self.to_nltk_tree(child) for child in node.children])
		else:
			return node.orth_

	def to_nltk_tree_general(self, node, attr_list=("dep_", "pos_"), level=99999):
		"""Tranforms a Spacy dependency tree into an NLTK tree, with certain spacy tree node attributes serving
		as parts of the NLTK tree node label content for uniqueness.

		Args:
			node: The starting node from the tree in which the transformation will occur.
			attr_list: Which attributes from the Spacy nodes will be included in the NLTK node label.
			level: The maximum depth of the tree.

		Returns:
			A NLTK Tree (nltk.tree)
		"""

		# transforms attributes in a node representation
		value_list = [getattr(node, attr) for attr in attr_list]
		node_representation = "/".join(value_list)

		if level == 0:
			return node_representation

		if node.n_lefts + node.n_rights > 0:
			return Tree(node_representation, [self.to_nltk_tree_general(child, attr_list, level-1) for child in node.children])
		else:
			return node_representation 

	def test(self, sentence):
		doc = self.nlp(sentence)
		root = [token for token in doc if token.head == token][0]
		subject = list(root.lefts)[0]
		for descendant in subject.subtree:
			assert subject is descendant or subject.is_ancestor(descendant)
			self.main_topic += str(descendant)+" "
		print(self.main_topic)

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

	test = Extractor()

	question = input("Enter a question, tape 'end' to finish \n")

	while not question == "end":
		print("custome rule: ")
		test.extract(str(question))
		test.test_3_rules(str(question))
		question = input("Enter a question, tape 'end' to finish \n")

