#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Enrico Biancotto
# Created Date: Wed March 1 2022
# =============================================================================
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

class VAD:
   # Class constructor
   def __init__(self, index):
      # Input file specs
      self.inputFileName = "input/inputaudio" + str(index) + ".data"
      # Output file specs
      self.outputFileName = "output/outputVAD" + str(index) + ".data"
      
      # Check existance of inputFile
      if not os.path.isfile(self.inputFileName):
         sys.exit("Error: "+ self.inputFileName + " file does not exists on the current directory!")

      # read bytes from file
      with open(self.inputFileName, "rb") as file:
         self.inputDataByte = bytearray(file.read())

      # -------------- CONSTANTS ----------------

      # 1 PACKET = 20 ms of track = 160 SAMPLE * 8bit x SAMPLE
      self.PACKET_SIZE = 160
      self.NUM_PACKETS = int(ceil(len(self.inputDataByte) / self.PACKET_SIZE))

      # Root Mean Square energy = sqrt(1/n * sum with i=[0, n] of x^2(i))
      self.signals_rmse = []
      self.signals_speech_energy = []
      self.signals_rumor_energy = []
      self.signals_threshold = []

      # Rumore info 
      self.SPEECH_ENERGY = 0.0
      self.RUMOR_ENERGY = 0.0
      self.INIT_RUMOR_ENERGY = 0.0

      # Lambda is a scaling factor parameter for threshold, Lambda should be in range [0.950, ... ,0.999].
      self.INIT_LAMBDA = 0.955
      self.LAMBDA = self.INIT_LAMBDA

      # threshold based on energy levels
      self.THRESHOLD = 0.0

      # count 5 INACTIVE SAMPLES before clipping packet
      self.MAX_INACTIVE_SAMPLES = 4
      self.INACTIVE_SAMPLES = self.MAX_INACTIVE_SAMPLES
 
   # compute Root Mean Square Energy of sample
   def computeRMSE(self, startIndex):
      energySum = 0
      # compute sum of energy of packet
      for sampleIndex in range(startIndex, startIndex + self.PACKET_SIZE):
         if sampleIndex < len(self.inputDataByte):
            energySum += np.int8(self.inputDataByte[sampleIndex]) ** 2
      rmse = (energySum / self.PACKET_SIZE) ** 0.5
      return rmse

   # Threshold = ((1 - lambda) * Emax) + (lambda * Emin)
   def updateThreshold(self):
      tmp = ((1 - self.LAMBDA) * self.SPEECH_ENERGY) + (self.LAMBDA * self.RUMOR_ENERGY)
      if tmp < 0.05:
         tmp = 0.05
      self.THRESHOLD = tmp

   # update scaling factor lambda to make it resistant to variable background environment
   def updateLambda(self):
      tmp = (self.SPEECH_ENERGY - self.RUMOR_ENERGY) / self.SPEECH_ENERGY
      if tmp < 0.950 or tmp > 0.999:
         tmp = self.INIT_LAMBDA
      self.LAMBDA = tmp

   # replace Packet with 0s in self.inputDataByte
   def replacePacket(self, startIndex):
      for index in range(startIndex, startIndex + self.PACKET_SIZE):
         if index < len(self.inputDataByte):
            self.inputDataByte[index] = np.int8(0)
   
   # compute Packet, startIndex = [0, 160, 320, ...]
   def computePacket(self, startIndex):
      #print(self.RUMOR_ENERGY, self.SPEECH_ENERGY)
      rmse = self.computeRMSE(startIndex)
      self.signals_rmse.append(rmse)
      
      if rmse > self.SPEECH_ENERGY:
         self.SPEECH_ENERGY = rmse
      elif rmse < self.RUMOR_ENERGY:
         if rmse == 0:
            self.RUMOR_ENERGY = self.INIT_RUMOR_ENERGY
         else:
            self.RUMOR_ENERGY = rmse
      
      self.updateLambda()
      self.updateThreshold()

      # save data for plot
      self.signals_speech_energy.append(self.SPEECH_ENERGY)
      self.signals_rumor_energy.append(self.RUMOR_ENERGY)
      self.signals_threshold.append(self.THRESHOLD)

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
            self.replacePacket(startIndex)
            self.INACTIVE_SAMPLES = self.MAX_INACTIVE_SAMPLES
      
   # Create outputVADN.data file where supprex packets are replaced by sequences of zeros of the same length
   def writeOutput(self):
      print("4) Write output to "+str(self.outputFileName) + "\n")
      np.array(self.inputDataByte, dtype=np.int8).astype(np.int8).tofile(self.outputFileName)

   # plot soundwave and energy levels of input signal
   def plot(self):
      print("5) Plot signal and Energy levels")
      plt.show()

      sig = np.frombuffer(self.inputDataByte, dtype=np.int8)
      plt.figure(1)

      plot_a = plt.subplot(211)
      plot_a.plot(sig)
      plot_a.set_xlabel('sample rate * time')
      plot_a.set_ylabel('energy')

      plot_b = plt.subplot(212)
      plot_b.plot(self.signals_rmse, color="b", label='RMS Energy')
      plot_b.plot(self.signals_speech_energy, color="g", label='Speech Energy')
      plot_b.plot(self.signals_rumor_energy, color="r", label='Rumor Energy')
      plot_b.plot(self.signals_threshold, color="m", label='Threshold')
      plot_b.legend(loc="upper left")
      plot_b.set_xlabel('time')
      plot_b.set_ylabel('energy')

      plt.show()

   # Analizzare il contenuto audio corrispondente a intervalli di 20 ms di segnale in forma sequenziale
   def analyze(self):
      print("1) Analyze file "+str(self.inputFileName) + "\n")
      # iterate first 2 packets to find background noise
      print("2) Analyze first 40ms to recognize background noise\n")
      maxIndex = self.PACKET_SIZE * 2   # 160 * 2 = 320 samples = 40 ms in the time domain
      for index in range(0, maxIndex, self.PACKET_SIZE):
         rmse = self.computeRMSE(index)
         self.signals_rmse.append(rmse)
         self.replacePacket(index)

      self.SPEECH_ENERGY = max(self.signals_rmse)
      if self.SPEECH_ENERGY == 0:
         self.SPEECH_ENERGY = 10e-7
      self.INIT_RUMOR_ENERGY = self.SPEECH_ENERGY / (1 + self.LAMBDA)
      self.RUMOR_ENERGY = self.INIT_RUMOR_ENERGY

      self.updateThreshold()

      self.signals_speech_energy.append(self.SPEECH_ENERGY)
      self.signals_rumor_energy.append(self.RUMOR_ENERGY)
      self.signals_threshold.append(self.THRESHOLD)

      # iterate over all frames that are complete
      print("3) Analyze the rest of the sequence\n")
      for index in range(maxIndex, len(self.inputDataByte), self.PACKET_SIZE):
         self.computePacket(index)
      
      # write bytes to .data file
      self.writeOutput()

      # plot rmse
      self.plot()


if __name__ == "__main__":
   # print informations
   __author__ = "Enrico Biancotto"
   __version__ = "1.0"
   __course__ = "Reti di Calcolatori"
   __homework__ = "1"
   __date__ = "01/04/2022"
   print('=' * 40)
   print('Author: ' + __author__)
   print('Version: ' + __version__)
   print('Course: ' + __course__)
   print('Homework: ' + __homework__)
   print('Date: ' + __date__)
   print('=' * 40 + "\n")

   # Read args passed from Command Line
   parser = argparse.ArgumentParser(description='Voice Activity Detection from inputaudio<N>.data file.')
   parser.add_argument('integer', type=int, metavar='<N>', help='Specify integer <N> to read from inputaudio<N>.data file ')
   i = parser.parse_args().integer
   
   # init VAD
   v = VAD(i)
   # start analysis of raw data
   v.analyze()