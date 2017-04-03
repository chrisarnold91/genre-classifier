import numpy as np

from config import *
from os import listdir
from madmom.utils.midi import MIDIFile
from pprint import pprint
from warnings import filterwarnings
from pitches import *
import pickle

CONSEC_DENOMS = 5
MAX_ONSET = 1000    # assume after 3 seconds, melody has finished

class Track():
    def __init__(self, name):
        self.name = name
        self.channels = {}
        self.pitch_var = {}
        self.pitch_diff_var = {}
        self.onset_diff_var = {}
        self.max_run = {}
        self.melody_channel = 0

    def choose_melody(self, setting):

        def key_with_max_value(d):
            return max(d, key=d.get)

        # print "PITCH VARIANCE"
        # pprint(self.pitch_var)
        # print "PITCH DIFFS VARIANCE"
        # pprint(self.pitch_diff_var)
        # print "ONSET DIFFS VARIANCE"
        # pprint(self.onset_diff_var)
        # print "MAX RUNS"
        # pprint(self.max_run)

        votes = []
        votes.append(key_with_max_value(self.pitch_var))
        votes.append(key_with_max_value(self.pitch_diff_var))
        votes.append(key_with_max_value(self.onset_diff_var))
        votes.append(key_with_max_value(self.max_run))
        votes.append(max(set(votes), key=votes.count))
        self.melody_channel = votes[setting]

        # print votes
        # print "MELODY: {}".format(self.melody_channel)

class Channel():
    def __init__(self, channel):
        self.channel = channel
        self.consecutives = {}
        self.onsets = []
        self.pitches = [] 
        # self.pattern_frequencies = {}
        self.runs = []

    def __str__(self):
        return "channel {} {} {}".format(self.channel, self.onsets, self.pitches)

    def add_onset(self, onset):
        self.onsets.append(onset)

    def add_pitch(self, pitch):
        self.pitches.append(pitch)

    def analyze_pitches(self):
        # print "analyzing pitches for channel {}".format(self.channel)
        return round(np.var(self.pitches), 2)

    def analyze_pitch_diffs(self):
        # print "analyzing pitch diffs for channel {}".format(self.channel)
        pitch_diffs = self.get_diffs(self.pitches)
        return round(np.var(pitch_diffs), 2)

    def analyze_onset_diffs(self):
        # print "analyzing onset diffs for channel {}".format(self.channel)
        onset_diffs = self.get_diffs(self.onsets)
        return round(np.var(onset_diffs), 2)

    def get_diffs(self, lst):
        # get differences between adjacent list elements
        diffs = []
        for i in range(1, len(lst)):
            diff = lst[i] - lst[i-1]
            if diff < MAX_ONSET:
                diffs.append(diff)
        return diffs

    def analyze_consec_pitches(self):
        # print "analyzing consecutive pitches for CHANNEL {}".format(self.channel)
        for c in range(1, CONSEC_DENOMS + 1):
            pattern_frequency = {}
            all_runs = {}
            for i in range(c):
                diffs = []
                runs = [0]
                for j in range(0, len(self.pitches) - c, c):
                    diff = self.pitches[i+j] - self.pitches[i+j-c]
                    if len(diffs) > 0:
                        if diff == diffs[-1]:
                            runs[-1] += 1
                        else:
                            runs.append(0)
                    diffs.append(diff)
                # count most occurring difference
                if diffs:
                    # most_occurring = max(set(diffs), key=diffs.count)
                    # frequency = diffs.count(most_occurring) / float(len(diffs))
                    # pattern_frequency[i] = round(frequency, 2)
                    # all_runs[i] = round(max(runs) / float(len(diffs)), 2)
                    self.runs.append(round(max(runs) / float(len(diffs)), 2))
            # self.pattern_frequencies[c] = pattern_frequency
            # self.runs[c] = all_runs
        # print(self.pattern_frequencies)
        # print(max(self.runs))

def main():
    filterwarnings('ignore')
    np.set_printoptions(suppress=True)
    np.set_printoptions(threshold=np.nan)
    np.set_printoptions(edgeitems=10)

    features = {}
    labels = {}
    training_hashes = {}
    test_set = {}
    test_labels = {}

    training_hashes = pickle.load(open("hash4.p", "rb"))

    for setting in range(FEATURES):

        # for genre in GENRES:
        #     for file in listdir('midi-' + genre):
        #         if not file.startswith('.'):
        #             track = Track(file)
        #             notes = get_notes('midi-' + genre + '/' + file)
        #             analyze_voices(notes, track, setting)
        #             build_hashes(file, genre, training_hashes, track)

        # pickle.dump(training_hashes, open("hash{}.p".format(setting), "wb"))

        for genre in GENRES:
            for file in listdir('midi-' + genre):
                if not file.startswith('.'):
                    track = Track(file)
                    # empty the previous samples
                    sample_hashes = {}
                    notes = get_notes('midi-' + genre + '/' + file)
                    analyze_voices(notes, track, setting)
                    build_hashes(file, genre, sample_hashes, track)
                    _, genres = match(training_hashes, sample_hashes)
                    score = get_classical(genres)

                    if setting == 0:
                        labels[file] = [1,0] if genre == "classical" else [0,1]
                    features.setdefault(file, []).append(score)

        for file in listdir('test-set'):
            if not file.startswith('.'):
                track = Track(file)
                test_hashes = {}
                notes = get_notes('test-set' + '/' + file)
                analyze_voices(notes, track, setting)
                build_hashes(file, 'test', test_hashes, track)
                _, genres = match(training_hashes, test_hashes)
                score = get_classical(genres)

                # if setting == 0:
                #     test_labels[file] = [1,0] if genre == "classical" else [0,1]
                test_set.setdefault(file, []).append(score)

    export_table(features, FEATURES_FILE)
    export_table(labels, LABELS_FILE)
    export_table(test_set, TEST_FILE)
    # export_table(test_labels, TEST_LABELS_FILE)

def get_classical(genres):
    if not genres or 'classical' not in genres:
        return 0
    if 'rock' not in genres:
        return 1
    total = genres['classical'] + genres['rock']
    return genres['classical'] / float(total)

def analyze_voices(notes, track, setting):
    for note in notes:
        c = note[CHANNEL]
        if c not in track.channels:
            track.channels[c] = Channel(c)
        track.channels[c].add_onset(note[ONSET])
        track.channels[c].add_pitch(note[PITCH])

    for channel_name, channel in track.channels.items():
        track.pitch_var[channel_name] = channel.analyze_pitches()
        track.pitch_diff_var[channel_name] = channel.analyze_pitch_diffs()
        track.onset_diff_var[channel_name] = channel.analyze_onset_diffs()
        track.max_run[channel_name] = channel.analyze_consec_pitches()
    
    track.choose_melody(setting)

def build_hashes(file, genre, hashes, track):
    if genre != 'test':
        file_name = 'midi-' + genre + '/' + file
    else:
        file_name = 'test-set/' + file

    midi = MIDIFile.from_file(file_name)
    notes = midi.notes(unit='ticks')

    # filter melody notes only
    melody = np.array([n for n in notes if n[CHANNEL] == track.melody_channel])

    # filter on most occurring note in melody
    peak = get_most_frequent_note(melody[:,PITCH])
    most_frequent = np.array([n for n in melody if n[PITCH] == peak])

    hash_time_diff(file, genre, hashes, most_frequent)

if __name__ == '__main__':
    main()
