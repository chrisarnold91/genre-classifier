import warnings

from os import listdir
from madmom.utils.midi import MIDIFile
from config import *


def main():
    warnings.filterwarnings('ignore')

    training_hashes = {}
    for genre in GENRES:
        for training_file in listdir('midi-' + genre):
            if not training_file.startswith('.'):
                build_hash_table(training_file, training_hashes, genre)

def build_hash_table(file, hashes, genre):
    print 'analyzing pitches for ' + file

    if genre != 'sample':
        file_name = 'midi-' + genre + '/' + file
    else:
        file_name = 'test-set/' + file

    midi = MIDIFile.from_file(file_name)
    notes = midi.notes(unit='ticks')

    ticks_per_bar = get_ticks_per_bar(midi, file)
    if ticks_per_bar == None:
        return first_notes

    bass_notes = get_bass(notes, ticks_per_bar)
    

def get_bass(notes, ticks_per_bar):
    bass_notes = {}
    lowest = 127

    for note in notes:
        if note[ONSET] % ticks_per_bar == 0:
            if note[ONSET] in first_notes:
                if note[PITCH] < first_notes[note[ONSET]]:
                    first_notes[note[ONSET]] = note[PITCH]
            else:
                first_notes[note[ONSET]] = note[PITCH]
    return bass_notes


if __name__ == '__main__':
    main()