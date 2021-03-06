import numpy as np
import pickle

from config import *
from os import listdir
from madmom.utils.midi import MIDIFile
from pprint import pprint
from pitches import *

CONSEC_DENOMS = 5
MAX_ONSET = 1000    # assume after 3 seconds, melody has finished
SETTINGS = 5

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

        votes = []
        votes.append(key_with_max_value(self.pitch_var))
        votes.append(key_with_max_value(self.pitch_diff_var))
        votes.append(key_with_max_value(self.onset_diff_var))
        votes.append(key_with_max_value(self.max_run))
        votes.append(min(set(votes), key=votes.count))
        self.melody_channel = votes[setting]

class Channel():
    def __init__(self, channel):
        self.channel = channel
        self.consecutives = {}
        self.onsets = []
        self.pitches = [] 

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
        runs = [0]
        for c in range(1, CONSEC_DENOMS + 1):
            pattern_frequency = {}
            all_runs = {}
            for i in range(c):
                diffs = []
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
                    runs.append(round(max(runs) / float(len(diffs)), 2))

        return (max(runs), len(self.pitches))

def main():

    load_settings()

    global H_FUNCTIONS
    H_FUNCTIONS = [hash_time_diff, hash_time_diff_percentile, hash_time_diff_pitch,\
    hash_time_diff_pitch_percentile]

    features = LastUpdatedOrderedDict()

    # build hashes
    for h in range(len(H_FUNCTIONS)):
        for setting in range(SETTINGS):

            training_hashes = {}
            hash_file = 'melody_hash{}-{}.p'.format(h, setting)
            hash_file_path = 'pickles/' + hash_file

            # build hashes from training set
            if hash_file not in listdir('pickles'):
                for genre in GENRES:
                    for file in listdir('midi-' + genre):
                        if not file.startswith('.'):
                            file_name = 'midi-' + genre + '/' + file
                            print "building hashes {} for {} with setting {}".format(h, file_name, setting)
                            track = Track(file)
                            notes = get_notes(file_name)
                            analyze_voices(notes, track, setting)
                            build_hashes(h, file, genre, training_hashes, track)

                pickle.dump(training_hashes, open(hash_file_path, "wb"))

    # classify tracks with hashes calculated above
    for h in range(len(H_FUNCTIONS)):

        melody_file = 'melody_features{}.csv'.format(h)
        melody_path = 'features/' + melody_file

        if melody_file not in listdir('features'):
            for setting in range(SETTINGS):

                hash_file = 'melody_hash{}-{}.p'.format(h, setting)
                hash_file_path = 'pickles/' + hash_file
                training_hashes = pickle.load(open(hash_file_path, "rb"))

                for genre in GENRES:
                    for file in listdir('midi-' + genre):
                        if not file.startswith('.'):
                            file_name = 'midi-' + genre + '/' + file
                            print "using hash {}, classifying {} with setting {}".format(h, file_name, setting)
                            track = Track(file)
                            # empty the previous samples
                            sample_hashes = {}
                            notes = get_notes(file_name)
                            analyze_voices(notes, track, setting)
                            build_hashes(h, file, genre, sample_hashes, track)
                            _, genres = match(training_hashes, sample_hashes)
                            score = get_classical(genres)
                            features.setdefault(file, []).append(score)

            export_table(features, melody_path)

    # classify test set tracks
    for h in range(len(H_FUNCTIONS)):

        test_file = 'test-features{}.csv'.format(h)
        test_set = LastUpdatedOrderedDict()

        for setting in range(SETTINGS):

            hash_file = 'melody_hash{}-{}.p'.format(h, setting)
            hash_file_path = 'pickles/' + hash_file
            training_hashes = pickle.load(open(hash_file_path, "rb"))

            for file in listdir('test-set'):
                if not file.startswith('.'):
                    print "testing hash {} on {} with setting {}".format(h, file, setting)
                    track = Track(file)
                    test_hashes = {}
                    notes = get_notes('test-set/' + file)
                    analyze_voices(notes, track, setting)
                    build_hashes(h, file, 'test', test_hashes, track)
                    _, genres = match(training_hashes, test_hashes)
                    score = get_classical(genres)
                    test_set.setdefault(file, []).append(score)

        export_table(test_set, 'test-features/' + test_file)

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

def build_hashes(h, file, genre, hashes, track):
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

    H_FUNCTIONS[h](file, genre, hashes, most_frequent)

if __name__ == '__main__':
    main()
