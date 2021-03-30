#import all required Library
import io
import pickle
import numpy as np
from scipy.io.wavfile import read
from sklearn import mixture
import warnings
warnings.filterwarnings("ignore")
import glob
import numpy as np
import os
import noisereduce as nr
import time
import numpy as np
from sklearn import preprocessing
import python_speech_features as mfcc

class AudioRec:
  """
  You should create 3 folders: one for store signatures of speakers modelpath='Audios/Models'
                               second for put file for check speaker testpath='Audios/Test/'
                               third for load trainig samples.trainpath='Audios/Train'
  The AudioRec Class is used to either recognize speaker or store his signature.
  It's initialized by threshold default =-27, remove_noise default = True, Path to store signatures  modelpath='Audios/Models'
  Path to speaker sound is testpath='Audios/Test/', path to extracted features from training samples trainpath='Audios/Train'
  
  It contains two main function  
   1. Check_audio: takes sound file and return either Id/Name of recognized 
      speaker or message undefined speaker or in case no pre-stored speakers DB is empty.
   
   2. Store_speaker it get the Id/Name and optional train path then it goto the training path, extract all audio file *.wav 
      that contains Id/Name and extract the signature and stored it in the speaker models.
  """

  def __init__(self, thresh = -27, remove_noise = True, modelpath='Audios/Models', testpath='Audios/Test/', trainpath='Audios/Train'):
    self.thresh=thresh
    self.remove_noise=remove_noise
    self.modelpath=modelpath
    self.testpath=testpath
    self.trainpath=trainpath

  def check_audio(self, file_name):
    modles_files= os.listdir(self.modelpath)
    if len(modles_files)==0:
      return (' There is no pre-stored speakers ')
    gmm_files = [os.path.join(self.modelpath,fname) for fname in 
              os.listdir(self.modelpath) if fname.endswith('.gmm')]
   
    models    = [pickle.load(open(fname,'rb')) for fname in gmm_files]

    speakers   = [fname.split(".gmm")[0] for fname      in gmm_files]
     
    sr,audio = read( self.testpath+file_name)
       #Remove Noise
    if self.remove_noise:
      noisy_part = audio[10000:15000]
      audio = nr.reduce_noise(audio_clip=audio.astype(float), prop_decrease=1.0, noise_clip=noisy_part.astype(float), verbose=False)

    vector   = self.extract_features(audio,sr)
    log_likelihood = np.zeros(len(models)) 
    
    for i in range(len(models)):
      gmm    = models[i]         #checking with each model one by one
      scores = np.array(gmm.score(vector))
      log_likelihood[i] = scores.sum()
   
    score=np.max(log_likelihood[:])
    winner = np.argmax(log_likelihood)
    
    print('Score: %f' % score)
    if score >= self.thresh:
      s = speakers[winner]
      return  s.split('/')[-1].capitalize()
    else:
      return 'Unknown Person'  
 
  def calculate_delta(self, array):
    """"Calculate and returns the delta of given feature vector matrix"""

    rows,cols = array.shape
    deltas = np.zeros((rows,20))
    N = 2
    for i in range(rows):
        index = []
        j = 1
        while j <= N:
            if i-j < 0:
                first = 0
            else:
                first = i-j
            if i+j > rows -1:
                second = rows -1
            else:
                second = i+j
            index.append((second,first))
            j+=1
        deltas[i] = ( array[index[0][0]]-array[index[0][1]] + (2 * (array[index[1][0]]-array[index[1][1]])) ) / 10
    return deltas
  
  def extract_features(self, audio, rate):
    """"extract 20 dim mfcc features from an audio, performs CMS and combines 
    delta to make it 40 dim feature vector"""    
    
    mfcc_feat = mfcc.mfcc(audio,rate, 0.025, 0.01,20,appendEnergy = True)
    
    mfcc_feat = preprocessing.scale(mfcc_feat)
    delta = self.calculate_delta(mfcc_feat)
    combined = np.hstack((mfcc_feat,delta)) 
    return combined 
  
  def store_speaker(self, id):
    x=id
    print('Store sound signature of Speaker:', x)
    modles_files= os.listdir(self.modelpath)
    path = self.trainpath
    
    text_files = glob.glob(path + "/" + x + "/" + "*.wav")
    print('There are number of files are found for extract signature:', len(text_files), ' These Files are:', text_files)
    
    count = 1
    # Extracting features for each speaker (5 files per speakers)
    features = np.asarray(())
    for i in range(len(text_files)):
      path = text_files[i]
      # read the audio
      sr, audio = read(path) #(source + path)
      #Remove Noise
      if self.remove_noise:
        noisy_part = audio[10000:15000]
        audio = nr.reduce_noise(audio_clip=audio.astype(float),  prop_decrease=1.0,noise_clip=noisy_part.astype(float), verbose=False)
    
      # extract 40 dimensional MFCC & delta MFCC features
      vector   = self.extract_features(audio,sr)
    
      if features.size == 0:
        features = vector
      else:
        features = np.vstack((features, vector))
    
    # when features of 5 files of speaker are concatenated, then do model training
      if count ==  len(text_files):    
        gmm = mixture.GaussianMixture(n_components = 16, max_iter = 200, covariance_type='diag',n_init = 3)
        gmm.fit(features)
        
        # dumping the trained gaussian model
        picklefile = x.capitalize()+  ".gmm" #path.split("-")[0]+ '_Id ' + path[k+2:k+7]+".gmm"
        pickle.dump(gmm,open(self.modelpath + '/'+picklefile,'wb'))
        print ('+ modeling completed for speaker:',picklefile," with data point = ",features.shape )   
        features = np.asarray(())
        count = 0
      count = count + 1