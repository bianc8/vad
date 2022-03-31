Il programma accetta un parametro posizionale obbligatorio, passato come argomento al programma dalla linea di comando:
positional arguments:
  N           Specify integer <N> to read from inputaudio<N>.data file

python3 vad.py 2    analizza il file inputaudio2.data


Si può vedere un menu di help eseguendo il programma con argomento -h oppure --help:
Per esempio:
python3 vad.py --help