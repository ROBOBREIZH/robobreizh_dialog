from topic_extraction import Extractor
from NLPModule import NLPModule


if __name__ == "__main__":

	test = Extractor()
	nlp = NLPModule()

	question = input("Enter a question, tape 'end' to finish \n")

	while not question == "end":
		main_topic, sentence = test.extract(str(question))
		category = nlp.find_category(question)
		sentiment = nlp.sentiment_analysis(question)
		
		question = input("Enter a question, tape 'end' to finish \n")

