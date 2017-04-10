# import numpy as np
import sys
import pickle
import pprint
import warnings

from madmom.utils.midi import *
from os import listdir
from populate import *

TABLE_FILE = 'table.csv'
ONSET_TOLERANCE = 100       # milliseconds

TITLE = 0
GENRE = 1
ONSET = 2

def main():
    warnings.filterwarnings('ignore')

    master_table = pickle.load(open("table.p", "rb"))

    for file in listdir('test-set'):
        if not file.startswith('.'):

            matches = midi_classify('test-set/' + file, master_table)
            tally = tally_matches(matches)
            classification = classify_genre(tally)
            percentages = get_percentages(classification)

            print(file)
            print(percentages)

def midi_classify(file, master_table):
    midi = MIDIFile.from_file(file)
    notes = midi.notes(unit='ticks')

    ticks_per_bar = get_ticks_per_bar(midi, notes, file)
    if ticks_per_bar == None:
        return

    # keeps track of titles with similar interval spacings
    # each value is a list of (title, genre) tuples
    matches = {}

    # use time intervals as dictionary keys
    interval = 1

    prev_highest, prev_onset, cursor = get_highest(notes, 0, ticks_per_bar)

    while cursor < len(notes) - 1:
        highest, onset, cursor_moved_by = get_highest(notes, cursor, ticks_per_bar)
        # time_gap = onset - prev_onset

        # compare current highest note with previous highest note
        if prev_highest in master_table.keys() and highest in master_table.keys():
            m = []

            for x in master_table[prev_highest]:
                for y in master_table[highest]:
                    if x[TITLE] == y[TITLE]:
                        if 0 <= y[ONSET] - x[ONSET] - 1 <= ONSET_TOLERANCE:
                            m.append((x[TITLE], x[GENRE]))

        matches[interval] = m

        prev_highest = highest
        prev_onset = onset
        cursor += cursor_moved_by
        interval += 1

    return matches

# return a dict of time intervals: (dict of genre: counts)
def tally_matches(matches):
    tally = {}
    for key, value in matches.items():
        # use titles to avoid tallying the same title twice for the same genre
        titles = []
        sub_tally = {}
        for v in value:
            if v[TITLE] not in titles:
                titles.append(v[TITLE])
                sub_tally[v[GENRE]] = 1
            else:
                sub_tally[v[GENRE]] += 1
        tally[key] = sub_tally
    return tally

# return a dict of genres: tallies
def classify_genre(tally):
    classification = {}
    for _, v in tally.items():
        genres = []
        maximum = 0
        for key, value in v.items():
            if value > maximum:
                maximum = value
                genres = [key]
            elif value == maximum:
                # account for ties
                genres.append(key)
        for g in genres:
            if g not in classification.keys():
                classification[g] = 1.0 / len(genres)
            else:
                classification[g] += 1.0 / len(genres)
    return classification

# return a dict of genres: percentages
def get_percentages(classification):
    percentages = {}
    total = 0
    for key, value in classification.items():
        total += value
    for key, value in classification.items():
        percentages[key] = round(value / total, 2)
    return percentages

def match(file, table, master_table):
    TALLY[file] = {}

    for pitch, trial_pair in table.items():
        if pitch in master_table.keys():
            for master_pair in master_table[pitch]:
                if trial_pair[0][0] == master_pair[0]:
                    record_match(file, master_pair[1])

def record_match(file, genre):
    if genre not in TALLY[file].keys():
        TALLY[file][genre] = 1
    else:
        TALLY[file][genre] += 1

if __name__ == '__main__':
    main()
