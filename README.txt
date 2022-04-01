Il programma accetta un parametro posizionale obbligatorio, passato come argomento al programma dalla linea di comando:
positional arguments:
  N           Specify integer <N> to read from inputaudio<N>.data file

python3 vad.py 2    analizza il file inputaudio2.data


Si può vedere un menu di help eseguendo il programma con argomento -h oppure --help:
Per esempio:
python3 vad.py --help

Nella cartella input/* ci sono i file di ingresso al programma vad.py
Nella cartella output/* ci sono i vari output del programma vad.py
Nella cartella images/* si può vedere un plot delle onde sonore di ingresso e di uscita, e un plot dei livelli di energia dei vari file di ingresso.