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

FEATURE = 0

# 0: highest first note of each bar, tracking milliseconds
# 1: highest first note of each bar, tracking bars

def main():
    if len(sys.argv) != 2:
        print "usage: requires exactly one argument"
        return

    if int(sys.argv[1]) not in range(2):
        print "usage: argument must be within range(" + str(2) + ")"
        return

    FEATURE = int(sys.argv[1])

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
    export_table_old()

def midi_train(table, file, genre=""):
    midi = MIDIFile.from_file(genre + file)

    if genre != "":
        genre_trimmed = genre.split("-")[1][:-1]
        print genre + file

    else:
        genre_trimmed = "???"

    # first matrix column is the offset in ticks (milliseconds)
    notes = midi.notes(unit='ticks')

    ticks_per_bar = get_ticks_per_bar(midi, notes, file)
    if ticks_per_bar == None:
        return

    # wow the units check out!
    # bars_in_track = beats / beats_per_bar

    # cursor is the index (or row) of a note matrix
    cursor = 0

    while cursor < len(notes) - 1:
        highest, highest_onset, cursor_moved_by = get_highest(notes, cursor, ticks_per_bar)

        # if FEATURE == 0:
        #     add_note(table, highest, file, genre_trimmed, highest_onset)
        # elif FEATURE == 1:
        bar = highest_onset // ticks_per_bar
        add_note(table, highest, file, genre_trimmed, bar)
    
        cursor += cursor_moved_by

def get_ticks_per_bar(midi, notes, file):
    # total number of ticks divided by resolution (number of ticks per beat)
    beats = notes[-1][ONSET] / midi.resolution

    # find time signature numerator, only works for type 1 midi files
    # for type 1 midi, each channel (voice) is contained in its own track
    events = midi.tracks[0].events
    event_index = find_event(events, TimeSignatureEvent)
    if event_index == None:
        print 'Time Signature not found for {}'.format(file)
        return None

    beats_per_bar = events[event_index].data[ONSET]
    return beats_per_bar * midi.resolution


# return the highest note in the current bar and how many notes were parsed
def get_highest(notes, cursor, ticks_per_bar):
    cursor_moved_by = 0
    highest = 0
    highest_onset = 0
    onset = notes[cursor][ONSET]
    next_bar = onset + ticks_per_bar

    while notes[cursor][ONSET] < next_bar:
        if notes[cursor][ONSET] == onset:
            if notes[cursor][PITCH] > highest:
                highest = notes[cursor][PITCH]
                highest_onset = notes[cursor][ONSET]
        
        if cursor < len(notes) - 1:
            cursor += 1
            cursor_moved_by += 1
        else:
            break

    return highest, highest_onset, cursor_moved_by

def add_note(table, pitch, file, genre_trimmed, onset):
    # add to table if it's a new pitch
    if pitch not in table.keys():
        table[pitch] = [(file, genre_trimmed, onset)]

    # append if pitch already exists as a key
    else:
        table[pitch].append((file, genre_trimmed, onset))

def find_event(events, event_type):
    for i in range(len(events)):
        if isinstance(events[i], event_type):
            return i
    return None

def export_table_old():
    file = open(TABLE_FILE, 'w')
    for tick, pitch_name_pairs in TABLE.items():
        row = str(tick) + SEPARATOR
        for pair in pitch_name_pairs:
            for value in pair:
                row += str(value) + SEPARATOR
            # row += str(pair[0]) + SEPARATOR + str(pair[1]) + SEPARATOR
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
