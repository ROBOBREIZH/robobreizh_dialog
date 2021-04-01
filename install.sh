#!/bin/bash

#Install and train the Question Classification module
sudo python3.7 -m pip install numpy 
sudo python3.7 -m pip install gensim 
sudo python3.7 -m pip install sklearn 

#Install Genderize library for genderization of Named Entity 
sudo python3.7 -m pip install Genderize 

#Install Transformers to perform context-based Question-Answering 
sudo python3.7 -m pip install transformers 

#Install spacy for tokenization
sudo python3.7 -m pip install spacy 
python3.7 -m spacy download en_core_web_sm

#Install wikipedia API
sudo python3.7 -m pip install wikipedia

#Install NLTK (used only on previous versions and/or futur versions)
sudo python3.7 -m pip install nltk 
python3.7 -c "import nltk; nltk.downloader.download('vader_lexicon');"

# CASA Dependencies
cd NLP_Server/CASA-Dialogue-Act-Classifier
sudo python3.7 -m pip install -r requirements.txt

#PyAudio
sudo apt install portaudio19-dev -y
sudo python2.7 -m pip install PyAudio 
sudo python2.7 -m pip install SpeechRecognition 

#DialogTag
cd ./NLP_Server/DialogTag
pip install -e .

