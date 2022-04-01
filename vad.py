#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Enrico Biancotto
# Created Date: Wed March 1 2022
# =============================================================================
__author__   = "Enrico Biancotto"
__version__  = "1.0"
__course__   = "Reti di Calcolatori"
__homework__ = "1"
__date__     = "01/04/2022"
"""
Python VAD implementation.

Example:
    $ python3 vad.py 1

Attributes:
   <N> (int): Specify integer <N> to read from inputaudio<N>.data file

"""
# =============================================================================
# Imports
# =============================================================================
import os
import sys
import argparse
import numpy as np
from math import ceil
from matplotlib import pyplot as plt
from matplotlib import gridspec as gridspec

class VAD:
   # Class constructor
   def __init__(self, index):
      """
      The __init__ method initiate the VAD class, setting defaults for variables and reading from inputFile.

      Args:
         index (:obj:`int`): `index` specify from which inputaudio<index>.data file to read from input.
      """
      self.fileIndex = index
      # Input file specs
      self.inputFileName =  f'input/inputaudio{str(index)}.data'
      # Output file specs
      self.outputFileName = "output/outputVAD" + str(index) + ".data"
      
      # Check existance of inputFile
      if not os.path.isfile(self.inputFileName):
         sys.exit("Error: "+ self.inputFileName + " file does not exists on the current directory!")

      # save original sound wave
      with open(self.inputFileName, "rb") as file:
         self.originalDataByte = bytearray(file.read())
      
      # read bytes from inputFile
      with open(self.inputFileName, "rb") as file:
         self.inputDataByte = bytearray(file.read())
      
      # Normalize input data
      self.outputDataDec = [] # Working data
      self.normalizedAudio = [] # Normalized list
      for sample in self.inputDataByte:
         self.outputDataDec.append(np.int8(sample))# read signed int8 from byte
         ret = float(np.int8(sample) / 128)     # normalize
         self.normalizedAudio.append(ret)

      # -------------- VARIABLES  ----------------

      # 1 PACKET = 20 ms of track = 160 bytes = 160 sample
      self.PACKET_SIZE = 160
      self.NUM_PACKETS = int(ceil(len(self.inputDataByte) / self.PACKET_SIZE))

      # Util plot lists
      # Root Mean Square Energy = sqrt(1/n * sum with i=[0, n] of x^2(i))
      self.signals_rmse = []
      self.signals_speech_energy = []
      self.signals_rumor_energy = []
      self.signals_threshold = []

      # Energy specs
      self.SPEECH_ENERGY = 0.0
      self.RUMOR_ENERGY = 0.0
      self.INIT_RUMOR_ENERGY = 0.0

      # Lambda is a scaling factor parameter for threshold, Lambda should be in range [0.950, ... ,0.999].
      self.INIT_LAMBDA = 0.955
      self.LAMBDA = self.INIT_LAMBDA

      # threshold based on energy levels
      self.THRESHOLD = 0.0

      # count 4 INACTIVE SAMPLES before clipping packet
      self.MAX_INACTIVE_SAMPLES = 4
      self.INACTIVE_SAMPLES = self.MAX_INACTIVE_SAMPLES

   # compute Root Mean Square Energy of sample
   def __computeRMSE(self, startIndex):
      energySum = 0
      totalPacket = 0
      for sampleIndex in range(startIndex, startIndex + self.PACKET_SIZE):
         if sampleIndex < len(self.normalizedAudio): # check for samples of last packet
            energySum += self.normalizedAudio[sampleIndex] ** 2
            totalPacket += 1
      rmse = (energySum / totalPacket) ** 0.5
      return rmse

   # Threshold = ((1 - lambda) * self.SPEECH_ENERGY) + (lambda * self.RUMOR_ENERGY)
   def __updateThreshold(self):
      tmp = ((1 - self.LAMBDA) * self.SPEECH_ENERGY) + (self.LAMBDA * self.RUMOR_ENERGY)
      if tmp < 0.05:
         tmp = 0.05
      self.THRESHOLD = tmp

   # update scaling factor lambda to make it resistant to variable background environment
   def __updateLambda(self):
      tmp = (self.SPEECH_ENERGY - self.RUMOR_ENERGY) / self.SPEECH_ENERGY
      if tmp < 0.950 or tmp > 0.999:
         tmp = self.INIT_LAMBDA
      self.LAMBDA = tmp

   # increase rumor_energy every iteration
   def __increaseRumor(self, index):
      self.RUMOR_ENERGY = self.RUMOR_ENERGY * (1.001 ** index)

   # replace Packet with 0s in self.normalizedAudio
   def __replacePacket(self, startIndex):
      for index in range(startIndex, startIndex + self.PACKET_SIZE):
         if index < len(self.outputDataDec):
            self.outputDataDec[index] = 0
   
   # compute Packet, startIndex = [0, 160, 320, ...]
   def __computePacket(self, startIndex):
      #print(self.RUMOR_ENERGY, self.SPEECH_ENERGY)
      rmse = self.__computeRMSE(startIndex)
      self.signals_rmse.append(rmse)
      
      if rmse > self.SPEECH_ENERGY:
         self.SPEECH_ENERGY = rmse
      if rmse < self.RUMOR_ENERGY:
         if rmse == 0:
            self.RUMOR_ENERGY = self.INIT_RUMOR_ENERGY
         else:
            self.RUMOR_ENERGY = rmse
      
      self.__updateLambda()
      self.__updateThreshold()

      # save data for plot
      self.signals_speech_energy.append(self.SPEECH_ENERGY)
      self.signals_rumor_energy.append(self.RUMOR_ENERGY)

      # if rmse > threshold it is voice, reset inactive_samples count
      if rmse > self.THRESHOLD:
         self.INACTIVE_SAMPLES = self.MAX_INACTIVE_SAMPLES
      # it is not voice, check for clipping
      else:
         # do not clip
         if self.INACTIVE_SAMPLES > 0:
            self.INACTIVE_SAMPLES -= 1
         # clip
         else:
            self.__replacePacket(startIndex)
      
      self.__increaseRumor(ceil(startIndex % self.PACKET_SIZE))
      
   # Create outputVADN.data file where supprex packets are replaced by sequences of zeros of the same length
   def __writeOutput(self):
      print("4) Write output to "+str(self.outputFileName) + "\n")
      self.outputData = np.array(self.outputDataDec, dtype=np.int8).astype(np.int8)
      self.outputData.tofile(self.outputFileName)

   # plot soundwave and energy levels of input signal
   def __plot(self):
      print("5) Plot signal and Energy levels")
      
      gs = gridspec.GridSpec(3, 1)
      fig = plt.figure()
      fig.tight_layout()
      
      # plot input sound wave
      sig = np.frombuffer(self.originalDataByte, dtype=np.int8)
      plot_a = fig.add_subplot(gs[0,0]) # row 0 col 0
      plot_a.set_ylabel('energy')
      plot_a.plot(sig)
      plot_a.title.set_text('Input Sound Wave')

      # plot output sound wave
      plot_b = fig.add_subplot(gs[1,0]) # row 1 col 0
      sig = np.frombuffer(self.outputData, dtype=np.int8)
      plot_b.plot(sig)
      plot_b.set_ylabel('energy')
      plot_b.title.set_text('Output Sound Wave')

      # plot Energy levels
      plot_c = fig.add_subplot(gs[2,0]) # row 2 col 0
      plot_c.plot(self.signals_rmse, color="b", label='RMS Energy')
      plot_c.plot(self.signals_speech_energy, color="g", label='Speech Energy')
      plot_c.plot(self.signals_rumor_energy, color="r", label='Rumor Energy')
      plot_c.legend(loc="upper left")
      plot_c.set_ylabel('energy')
      plot_c.title.set_text('Energy Levels')
      
      # Save to image
      plt.subplots_adjust(left=0.05, bottom=0.055, right=0.98, top=0.94, wspace=0.206, hspace=0.565)
      name = "images/inputaudio_" + str(self.fileIndex) + ".png"
      plt.savefig(name)
      plt.show()

   # Analizzare il contenuto audio corrispondente a intervalli di 20 ms di segnale in forma sequenziale
   def analyze(self):
      """
      The __init__ method initiate the VAD class, setting defaults for variables and reading from inputFile.

      Args:
         index (:obj:`int`): `index` specify from which inputaudio<index>.data file to read from input.
      """
      print("1) Analyze file "+str(self.inputFileName) + "\n")

      # iterate over the first 2 packets to find energy levels and threshold of the background noise
      print("2) Analyze first 40ms to recognize background noise\n")
      maxIndex = self.PACKET_SIZE * 2   # 160 * 2 = 320 samples = 40 ms in the time domain
      for index in range(0, maxIndex, self.PACKET_SIZE):
         rmse = self.__computeRMSE(index)
         self.signals_rmse.append(rmse)
         self.__replacePacket(index)

      # update values
      self.SPEECH_ENERGY = max(self.signals_rmse)
      if self.SPEECH_ENERGY == 0:
         self.SPEECH_ENERGY = 10e-6
      self.INIT_RUMOR_ENERGY = self.SPEECH_ENERGY / (1 + self.LAMBDA)
      self.RUMOR_ENERGY = self.INIT_RUMOR_ENERGY

      self.__updateThreshold()

      # save data for plot
      self.signals_speech_energy.append(self.SPEECH_ENERGY)
      self.signals_rumor_energy.append(self.RUMOR_ENERGY)

      # iterate over all the remaining packets
      print("3) Analyze the rest of the sequence\n")
      for index in range(maxIndex, len(self.inputDataByte), self.PACKET_SIZE):
         self.__computePacket(index)
      
      # write bytes to .data file
      self.__writeOutput()

      # plot rmse
      self.__plot()


if __name__ == "__main__":
   # print informations
   print('=' * 40)
   print('Author: '  + __author__)
   print('Version: ' + __version__)
   print('Course: '  + __course__)
   print('Homework: '+ __homework__)
   print('Date: ' + __date__)
   print('=' * 40 + "\n")

   # Read args passed from Command Line
   parser = argparse.ArgumentParser(description='Voice Activity Detection from inputaudio<N>.data file.')
   parser.add_argument('integer', type=int, metavar='<N>', help='Specify integer <N> to read from inputaudio<N>.data file ')
   fileIndex = parser.parse_args().integer
   
   # init VAD
   v = VAD(fileIndex)
   # start analysis of raw data
   v.analyze()