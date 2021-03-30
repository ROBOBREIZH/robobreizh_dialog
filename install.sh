#!/bin/bash

#Install and train the Question Classification module
pip3 install numpy -y
pip3 install gensim -y 
pip3 install sklearn -y
cd Question_Classification/data
wget --save-cookies cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1saFGKezSFgH-5YjsQX_yiWes41xqbHrf' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p' >> tmp.txt
code=`cat tmp.txt`
wget --load-cookies cookies.txt 'https://docs.google.com/uc?export=download&confirm='$code'&id=1saFGKezSFgH-5YjsQX_yiWes41xqbHrf' -O glove.txt
rm tmp.txt
rm cookies.txt
cd .. 
python3.7 train.py

#Install Genderize library for genderization of Named Entity 
pip3 install Genderize -y

#Install Transformers to perform context-based Question-Answering 
pip3 install transformers -y

#Install spacy for tokenization
pip3 install spacy -y
python3.7 -m spacy download en_core_web_sm

#Install wikipedia API
pip3 install wikipedia -y

#Install NLTK (used only on previous versions and/or futur versions)
pip3 install nltk -y
python3.7 -c "import nltk; nltk.downloader.download('vader_lexicon');"

# CASA Dependencies
cd nlp/CASA-Dialogue-Act-Classifier
sudo python3.7 -m pip install -r requirements.txt
