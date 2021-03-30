#!/bin/bash

#Install and train the Question Classification module
pip3 install numpy
pip3 install gensim
pip3 install sklearn
cd Question_Classification/data
wget --save-cookies cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1saFGKezSFgH-5YjsQX_yiWes41xqbHrf' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p' >> tmp.txt
code=`cat tmp.txt`
wget --load-cookies cookies.txt 'https://docs.google.com/uc?export=download&confirm='$code'&id=1saFGKezSFgH-5YjsQX_yiWes41xqbHrf' -O glove.txt
rm tmp.txt
rm cookies.txt
cd .. 
python train.py

#Install Genderize library for genderization of Named Entity 
pip3 install Genderize

#Install Transformers to perform context-based Question-Answering 
pip3 install transformers

#Install spacy for tokenization
pip3 install spacy
python3.6 -m spacy download en_core_web_sm

#Install wikipedia API
pip3 install wikipedia

#Install NLTK (used only on previous versions and/or futur versions)
pip3 install nltk
