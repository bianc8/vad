from math import ceil 
import numpy as np 
import sys

def createDecimalAudio(input):
   file = open(str(input)+'.data', 'rb')
   myBinaryAudio = bytearray(file.read())
   file.close()
   myDecimalAudio = []
   for i in myBinaryAudio:
      myDecimalAudio.append(np.int8(i))
   return myDecimalAudio

def normalizeDecimalAudio(input):
   myNormalizedAudio = []
   for i in input:
      tmp = i/128
      myNormalizedAudio.append(float(tmp))
   return myNormalizedAudio

def computeThreshold(eMax, eMin, lbd):
   tmp = ((1-lbd)*eMax) + (lbd*eMin)
   #set a default threshold value for the first frames
   if(tmp < 0.05): 
      tmp = 0.05
   return tmp

def updateLbd(eMax, eMin):
   tmp = (eMax - eMin) / eMin
   if(tmp < 0.950 or tmp >= 1):
      return 0.955
   return tmp

def update_eMin(eMin, index): #function which slightly update eMin
   return eMin * (1.001 ** index)

def computeAudio(arg):
   n = arg
   inputA = 'inputaudio'+str(n) 
   decimalAudio = createDecimalAudio("input/"+inputA)
   normalizedAudio = normalizeDecimalAudio(decimalAudio)

   #CONSTANTS
   NS_X_PACKET = 160 # n of samples x packet 
   sampsPerFrame = 160 # n of samples x frame
   nSamples = len(normalizedAudio)
   nFrames = int(ceil(nSamples / NS_X_PACKET)) #number of samples in f'{input}.data'
   RMS_energy = [] # list of root mean square energy of each frame

   #PRECODING
   #compute the RMSE of the first 2 frames => total delay = 2 * 20ms = 40ms < 50ms 
   for i in range(2): #! aggiungere controllo se nFrames < 2
      start_p = i * sampsPerFrame
      tmp_val = 0.0
      for j in range(sampsPerFrame):
         tmp_val += (normalizedAudio[start_p + j]) ** 2 # sum the energy of each sample in i frame
      tmp_val = tmp_val / sampsPerFrame # compute energy mean
      RMS_energy.append(tmp_val ** 0.5) # compute square root

   #initialize parameters to compute treshold
   lbd = 0.955 
   eMax = max(RMS_energy)
   if(eMax == 0):
      eMax = 10e-6
   eMin =  eMax / (lbd+1) 
   intial_eMin = eMin # default value for eMin
   threshold = computeThreshold(eMax, eMin, lbd)
   #set the first two frames as "not speech"
   flag_list = [0, 0]
   inactive_count = 5

   #PROCESS ALL THE COMPLETE FRAMES
   for i in range(2, nFrames-2, 1):
      start_p = i * sampsPerFrame # index of first sample for i frame
      #compute RMS energy of i frame
      curr_energy = 0.0 # energy of i frame
      for j in range(sampsPerFrame): # compute the energy of the frame
         curr_energy += normalizedAudio[start_p + j] ** 2
      curr_energy = curr_energy / sampsPerFrame # compute energy mean
      curr_energy = curr_energy ** 0.5 # compute square root

      #update threshold parameters
      if(curr_energy > eMax):
         eMax = curr_energy
      if(curr_energy < eMin):
         if(curr_energy == 0):
               eMin = intial_eMin
         else:
               eMin = curr_energy

      lbd = updateLbd(eMax, eMin)
      threshold = computeThreshold(eMax, eMin, lbd)

      #decide if current frame is (1):speech (0):not speech
      if(curr_energy > threshold): #frame = (1)
         inactive_count = 0
         flag_list.append(1)
      else: #frame = (0)
         if(inactive_count >= 4): #clipping ok 
               flag_list.append(0)
         else: #avoid clipping
               flag_list.append(1) 
               inactive_count += 1
      
      eMin = update_eMin(eMin, i)

   #PROCESS THE EVENTUALLY LAST INCOMPLETE FRAME
   tmp_energy = 0.0
   for i in range(len(normalizedAudio) % sampsPerFrame):
      start_p = nFrames-1
      tmp_energy += normalizedAudio[start_p + i] ** 2

   tmp_energy = tmp_energy / (len(normalizedAudio) % sampsPerFrame)
   tmp_energy = tmp_energy ** 0.5
   if(tmp_energy > eMax):
      eMax = tmp_energy
   if(tmp_energy < eMin):
      if(tmp_energy == 0):
         eMin = intial_eMin
      else:
         eMin = tmp_energy

   lbd = updateLbd(eMax, eMin)
   threshold = computeThreshold(eMin, eMax, lbd)
   if(tmp_energy > threshold):
      inactive_count = 0
      flag_list.append(1)
   else:
      if(inactive_count >= 4):
         flag_list.append(0)
      else:
         flag_list.append(1)
         inactive_count += 1
         
   #set the 'not speech' frames of decimalAudio to 0
   for i in range(len(flag_list)):
      if(flag_list[i] == 0):
         for j in range(sampsPerFrame):
               decimalAudio[i*sampsPerFrame + j] = 0

   #export flag list
   myFolder = "txtOutput/"
   with open(myFolder + 'output'+str(n)+'VAD.txt', "wb") as f:
      for i in range(len(flag_list)):
         f.write('Frame '+str(i)+': \t')
         f.write(str(flag_list[i]))
         if(flag_list[i] == 0):
            f.write('\t=> Not speech')
         else:
            f.write('\t=> Speech')
         f.write("\n")

   #export file .data
   export_ar = np.array(decimalAudio, dtype=np.int8)
   myFolder = "dataOutput/"
   export_ar.astype(np.int8).tofile(myFolder + 'outputaudio'+str(n)+'.data')

#MAIN
print("Inserire il numero (da 1 a 5) dell'audio da elaborare")
print("Esempio: per elaborare inputaudio1.data inserire 1")
s = 1
computeAudio(1)

