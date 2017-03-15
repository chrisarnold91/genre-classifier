import matplotlib.pyplot as plt
import warnings

from madmom.utils.midi import *
from os import listdir

GENRES = ['classical', 'rock']

ONSET = 0
PITCH = 1
DURATION = 2
VELOCITY = 3
CHANNEL = 4


def main():
    warnings.filterwarnings('ignore')
    np.set_printoptions(suppress=True)
    np.set_printoptions(threshold=np.nan)

    for genre in GENRES:
        for file in listdir('midi-' + genre):
            if not file.startswith('.'):
                print 'analyzing amplitudes for ' + file
                analyze_amplitude(file, genre)

def analyze_amplitude(file, genre):
    midi = MIDIFile.from_file('midi-' + genre + '/' + file)
    notes = midi.notes(unit='ticks')

    amplitudes = []
    onsets = []
    for note in notes:
        if note[ONSET] not in amplitudes:
            onsets.append(1)
            amplitudes.append(note[ONSET])
        else:
            onsets[-1] += 1

    plt.bar(range(len(onsets)), onsets, 1, color="blue")
    plt.title(file)
    plt.xlabel('amplitude')
    plt.ylabel('count')
    plt.savefig('amplitudes/' + file + '.png')
    # plt.show()
    plt.close()




if __name__ == '__main__':
    main()
