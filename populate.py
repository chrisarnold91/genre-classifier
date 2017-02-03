import numpy as np
# import tensorflow as tf
import pickle
import pprint
import warnings

from madmom.utils.midi import *
from os import listdir


TABLE_FILE = 'table.csv'
GENRES = ['midi-classical', 'midi-rock', 'midi-pop']
SEPARATOR = ','

TABLE = {}

ONSET = 0
PITCH = 1
DURATION = 2
VELOCITY = 3
CHANNEL = 4


def main():
    warnings.filterwarnings('ignore')

    np.set_printoptions(suppress=True)
    np.set_printoptions(threshold=np.nan)
    # np.set_printoptions(edgeitems=10)

    for genre in GENRES:
        for file in listdir(genre):
            if not file.startswith('.'):
                midi_train(TABLE, file, genre + '/')

    pprint.pprint(TABLE)
    pickle.dump(TABLE, open("table.p", "wb"))
    export_table()

def midi_train(table, file, genre=""):
    midi = MIDIFile.from_file(genre + file)

    if genre != "":
        genre_trimmed = genre.split("-")[1][:-1]
        print genre + file

    else:
        genre_trimmed = "???"

    # first matrix column is the offset in ticks (milliseconds)
    notes = midi.notes(unit='ticks')

    # total number of ticks divided by resolution (number of ticks per beat)
    beats = notes[-1][ONSET] / midi.resolution

    # find time signature numerator, only works for type 1 midi files
    # for type 1 midi, each channel (voice) is contained in its own track
    events = midi.tracks[0].events
    event_index = find_time_signature(events)
    if event_index == None:
        print 'Time Signature not found for {}'.format(file)
        return

    beats_per_bar = events[event_index].data[ONSET]
    ticks_per_bar = beats_per_bar * midi.resolution

    # wow the units check out!
    # bars = beats / beats_per_bar

    # remember current onset and its highest pitch so far
    curr = (notes[0][ONSET], notes[0][PITCH])

    for note in range(len(notes)):
        onset = notes[note][ONSET]
        pitch = notes[note][PITCH]

        # is this note at the beginning of the bar?
        if onset % ticks_per_bar == 0:

            # does this note have the same offset?
            if onset == curr[ONSET]:

                # look for the highest pitch for this onset
                if pitch > curr[PITCH]:
                    curr = (onset, pitch)

            # we've reached the next onset
            else:
                add_note(table, genre_trimmed, curr)
                curr = (onset, pitch)

    add_note(table, genre_trimmed, curr)

def add_note(table, genre_trimmed, curr):
    # add to table if it's a new pitch
    if curr[PITCH] not in table.keys():
        table[curr[PITCH]] = [(curr[ONSET], genre_trimmed)]

    # append if pitch already exists as a key
    else:
        table[curr[PITCH]].append((curr[ONSET], genre_trimmed))

def find_time_signature(events):
    for i in range(len(events)):
        if isinstance(events[i], TimeSignatureEvent):
            return i
    return None

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


#########################################################
# pitch references                                      #
#########################################################
# octave|c  |c# |d  |d# |e  |f  |f# |g  |g# |a  |a# |b  # 
#########################################################
#   0   |0  |1  |2  |3  |4  |5  |6  |7  |8  |9  |10 |11 #
#   1   |12 |13 |14 |15 |16 |17 |18 |19 |20 |21 |22 |23 #
#   2   |24 |25 |26 |27 |28 |29 |30 |31 |32 |33 |34 |35 #
#   3   |36 |37 |38 |39 |40 |41 |42 |43 |44 |45 |46 |47 #
#   4   |48 |49 |50 |51 |52 |53 |54 |55 |56 |57 |58 |59 #
#   5   |60 |61 |62 |63 |64 |65 |66 |67 |68 |69 |70 |71 #
#   6   |72 |73 |74 |75 |76 |77 |78 |79 |80 |81 |82 |83 #
#   7   |84 |85 |86 |87 |88 |89 |90 |91 |92 |93 |94 |95 #
#   8   |96 |97 |98 |99 |100|101|102|103|104|105|106|107#
#   9   |108|109|110|111|112|113|114|115|116|117|118|119#
#   10  |120|121|122|123|124|125|126|127|   |   |   |   #
#########################################################
