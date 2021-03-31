# Dialog_module

## Description

## 1. A conversational agent

### 1.1. Requirements

- Python >= 3.7
- pip3 for Python >= 3.7
- Ubuntu = 16.04

### 1.2. Installation

Be careful, the full installation can take some free space (at least 500MB), report if it's > 1GB.

Simply run 
```
sudo bash ./install.sh
```
and see what happened...

### 1.3. Usage

Simply run the script 
```
sudo ./NLPModule.py
```

Be careful, in the first execution the script must download some additionals models, such as:
```en_core_web_sm``` for Spacy and ```distilbert-base-uncased-distilled-squad``` & ```bert-large-cased-whole-word-masking-finetuned-squad``` for Transformers

Those models will also take some free space (around 600MB for all).

### 1.4. Tools used

Spacy:
https://spacy.io/

Transformers:
https://github.com/huggingface/transformers

Wikipedia Python API:
https://pypi.org/project/wikipedia/

Named Entity gender classifier:
https://pypi.org/project/Genderize/

NLTK (Natural Language ToolKit):
https://www.nltk.org/

## 2. An action detection module using Mbot 

### 2.1. Installation

Simply run the script 
```
sudo ./install_mbot.sh
```

### 2.2. Tools used

ROS (Robot Operating System):
https://www.ros.org/

Mbot :
https://github.com/socrob/mbot_natural_language_processing

Dataset:
https://github.com/kyordhel/GPSRCmdGen

## 3. Speaker recognition

**Tested on Ubuntu 20.04 and macOS 10.15 Catalina, Python 3.8.5**

WIP, Python testing scripts are hardcoded and may change soon.

### 3.1 Dependecies
```
cd Speaker_recognition
python3 -m pip install -r requirements.txt
```

### 3.2 Test dataset
You can use if you want this small dataset to test the program
```
./download_dataset.sh
```

### 3.3 Usage
First, you need to generate speaker models from the dataset

```
python3 generate_speaker_models.py
```

Then, you can start the speaker recognition testing script
```
python3 recognise_speaker.py
```

