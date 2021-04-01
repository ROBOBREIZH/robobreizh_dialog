# Robobreizh_dialog Package

## Description

## 1. A conversational agent

### 1.1. Requirements

- Python >= 3.7
- pip3 for Python >= 3.7
- Ubuntu = 16.04

### 1.2. Installation

#### 1.2.1. Sentence Analysis Module
Be careful, the full installation can take some free space (at least 500MB), report if it's > 1GB.

Simply run 
```buildoutcfg
sudo bash ./install.sh
```

#### 1.2.2. Comet-Commonsense

The installation will download 3GB of data (pretrained weights and models).

```buildoutcfg
cd NLP_Server/comet_commonsense/
sudo bash ./install.sh
```

### 1.3. Usage

#### 1.3.1. Sentence Analysis Server

This server can take a sentence as request and give back:
- The main topic
- The sentence category
- A global sentiment (positive/neutral/negative)

To launch it just run in a new terminal:
```buildoutcfg
cd ./NLP_Server
python3.7 main.py
```

Be careful, in the first execution the script must download some additionals models, such as:
```en_core_web_sm``` for Spacy and ```distilbert-base-uncased-distilled-squad``` & ```bert-large-cased-whole-word-masking-finetuned-squad``` for Transformers

Those models will also take some free space (around 600MB for all).

#### 1.3.2. Commonsense Intention Server

This module use the [Comet Model](https://github.com/atcbosselut/comet-commonsense) from the ConceptNet and Atomic dataset to retrieve Commonsense Intention from sentences.

To launch it run the script in a new terminal:

```buildoutcfg
cd ./NLP_Server/comet_commonsense
python3.7 intent_socket.py
```

#### 1.3.3. ROS Dialog Node

This Node is currently a implementation working with a computer in-built or plug-in Microphone (via the portaudio API). 
To launch it go to the source of the robobreizh_simu_ws and type:

```buildoutcfg
catkin_make
source devel/setup.bash
roslaunch dialog dialog.launch
```

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

Comet:
https://github.com/atcbosselut/comet-commonsense

## 2. An action detection module using Mbot 

### 2.1. Prerequisites

This module use Tensorflow with CUDA for training. If you want to do trianing you need CUDA 11 properly installed in your machine. See [CUDA Installation Doc](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html).

### 2.2. Installation

Simply run the script 
```
sudo ./install_mbot.sh
```

If you want to do training you also need to install others dependencies:
```
source mbot_natural_language_processing/mbot_nlu_training/common/setup/nlu_training_setup.sh
```

### 2.3. Tools used

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

