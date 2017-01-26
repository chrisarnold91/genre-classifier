import numpy as np
# import tensorflow as tf
import pickle
import pprint
import warnings

from madmom.utils.midi import *
from os import listdir


TABLE_FILE = 'table.csv'
CATEGORIES = ['midi-classical', 'midi-rock', 'midi-videogame']
SEPARATOR = ','

ONSET = 0
PITCH = 1
DURATION = 2
VELOCITY = 3
CHANNEL = 4

TABLE = {}


def main():
    warnings.filterwarnings('ignore')

    np.set_printoptions(suppress=True)
    np.set_printoptions(threshold=np.nan)
    # np.set_printoptions(edgeitems=10)

    for category in CATEGORIES:
        for file in listdir(category):
            if not file.startswith('.'):
                midi_train(TABLE, file, category + '/')

    pprint.pprint(TABLE)
    pickle.dump(TABLE, open("table.p", "wb"))
    export_table()

def midi_train(table, file, category=""):
    if category != "":
        print category + file

    midi = MIDIFile.from_file(category + file)

    # first matrix column is the offset in ticks (milliseconds)
    notes = midi.notes(unit='ticks')

    # total number of ticks divided by resolution (number of ticks per beat)
    beats = notes[-1][ONSET] / midi.resolution

    # find time signature numerator, only works for type 1 midi files
    # for type 1 midi, each channel (voice) is contained in its own track
    events = midi.tracks[0].events
    event_index = find_time_signature(events)
    if event_index == None:
        print 'Time Signature not found'
        return

    beats_per_bar = events[event_index].data[ONSET]
    ticks_per_bar = beats_per_bar * midi.resolution

    # wow the units check out!
    bars = beats / beats_per_bar

    for note in range(len(notes)):
        onset = notes[note][ONSET]
        pitch = notes[note][PITCH]

        # is this note at the beginning of the bar?
        if onset % ticks_per_bar == 0:

            if onset not in table.keys():
                table[onset] = []
                table[onset].append((pitch, file))

            else:
                highest = get_highest_pitch(table[onset], file)
                set_pitch(table[onset], file, pitch, highest)

def find_time_signature(events):
    for i in range(len(events)):
        if type(events[i]) == TimeSignatureEvent:
            return i
    return None

def get_highest_pitch(row, file):
    for tup in row:
        if tup[1] == file:
            return tup[0]
    return None

def set_pitch(row, file, pitch, highest):
    for tup in row:
        if tup[1] == file:
            # found new highest pitch?
            if pitch > highest:
                row.remove(tup)
                row.append((pitch, file))
            return
    row.append((pitch, file))

def export_table():
    file = open(TABLE_FILE, 'w')
    for tick, pitch_name_pairs in TABLE.items():
        row = str(tick) + SEPARATOR
        for pair in pitch_name_pairs:
            row += str(pair[0]) + SEPARATOR + str(pair[1]) + SEPARATOR
        row += '\n'
        file.write(row)


if __name__ == '__main__':
    main()
