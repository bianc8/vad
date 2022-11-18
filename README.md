# Example

![example of input audio](https://github.com/enricBiancott0/vad/raw/main/images/inputaudio_2.png)

# How it works

The goal of the program is to remove the background noise in a conversation, but just when there is no one speaking.

As we can see from the Example, the program, simulating a real time computation without cycling through the input multiple times, 
calculates the Energy of the noise and speaking signals and removes the blocks which does not have high energy

# How to execute

The program must have an index as argument, from 1 to 5, in order to select the input audio file from ./input/ folder
  python3 vad.py 2    to analyze inputaudio2.data file

You can see an Help menu via:
  python3 vad.py --help

## Other 

Output folder contains the output.data which can be opened with [VLC Media Player](https://www.videolan.org/vlc/)

Input folder contains given audio input .data files

Images folder contains a plot of the input and output audio waves, and corresponding energy levels.
