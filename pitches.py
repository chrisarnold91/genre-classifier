import matplotlib.pyplot as plt
import warnings
import pickle

from config import *
from sys import argv
from os import listdir
from madmom.utils.midi import MIDIFile
from heapq import nlargest
from pprint import pprint

# Shazam: https://www.ee.columbia.edu/~dpwe/papers/Wang03-shazam.pdf
# see Figure 3A (page 4) for the reasoning behind scatter plots

# Avery Wang describes Shazam's process of fingerprinting audio files to
# improve how efficiently they can be matched together. This is accomplished
# by analyzing peak frequencies, which take into account peak amplitudes
# sampled around 3 times per second, as well as the frequency at that
# particular point in time (in milliseconds).

# For this project, the goal is to classify music genres instead of finding a
# 1-to-1 match, and instead of using sound files, MIDI files are being used.
# Since MIDI doesn't take into account amplitude, I consider the most
# occuring note in a file to be a "peak frequency".

# genres being considered when classifying MIDI files
GENRES = ['classical', 'rock']

# most frequent pitches that occur in the MIDI file
TOP_MOST_FREQUENT = 1

# number of other peaks that each peak is paired to
FAN_FACTOR = 5

# indices for MIDI note attributes, according to the madmom library
ONSET = 0
PITCH = 1
DURATION = 2
VELOCITY = 3
CHANNEL = 4

# MIDI pitches are represented by a number from 0 to 127 (see table below)
PITCHES = {
    0: 'C',
    1: 'C#',
    2: 'D',
    3: 'D#',
    4: 'E',
    5: 'F',
    6: 'F#',
    7: 'G',
    8: 'G#',
    9: 'A',
    10: 'A#',
    11: 'B'
}

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

class Note():
    """
    A note that represents a note's midi pitch (from 0 to 127), its letter
    value and its octave (according to the pitch references table above)
    """
    def __init__(self, midi_pitch):
        """
        Creates a Note with the given midi_pitch.

        @param int midi_pitch: the note's midi pitch (from 0 to 127)
        @param str letter: the note's letter value
        @param int octave: the note's octave
        @rtype: None
        """
        self.midi_pitch = midi_pitch
        self.letter = PITCHES[midi_pitch % 12]
        self.octave = midi_pitch // 12

    def __repr__(self):
        """
        Represents a Note (self) as a string that is human readable, which
        includes the note's letter value and octave.

        @param PeakPair self: this peak pair
        @rtype: str
        """
        return '({},{},{})'.format(self.midi_pitch, self.letter, self.octave)

class PeakPair():
    """
    A peak pair that represents the relationship between two peak notes.
    """

    def __init__(self, onset, file_name, genre):
        """
        Create a PeakPair that occurs at onset time within file_name of a
        particular genre.

        @param str file_name: the MIDI file name in which the pair exists
        @param str genre: the genre of the MIDI file
        @param int onset: the timestamp of the pair within the MIDI file
        @rtype: None
        """
        self.file_name = file_name
        self.genre = genre
        self.onset = onset

    def __repr__(self):
        """
        Represents a PeakPair (self) as a string that can be written to the
        database.

        @param PeakPair self: this peak pair
        @rtype: str
        """
        return '({},{},{})'.format(self.onset, self.file_name, self.genre)

class Bucket():
    """
    A bucket that contains timestamps of hash matches between an individual
    training MIDI file and the sample MIDI file.

    === Attributes ===
    @param list[int] training_times: contains the timestamps of where the
        match occurs within the training MIDI file
    @param list[int] sample_times: contains the timestamps of where the
        match occurs within the sample MIDI file
    """

    def __init__(self):
        """
        Creates an empty bucket.

        @rtype: None
        """
        self._training_times = []
        self._sample_times = []

    def get_training_times(self):
        """
        Get the timestamps of the training time list.

        @param Bucket self: this bucket
        @rtype: list[int]
        """
        return self._training_times

    def get_sample_times(self):
        """
        Get the timestamps of the sample time list.
        
        @param Bucket self: this bucket
        @rtype: list[int]
        """
        return self._sample_times

    def add_training_time(self, time):
        """
        Add a timestamp to the training time list.

        @param Bucket self: this bucket
        @param int time: the timestamp at which the match occured in the
            training MIDI file
        @rtype: None
        """
        self._training_times.append(time)

    def add_sample_time(self, time):
        """
        Add a timestamp to the sample time list.

        @param Bucket self: this bucket
        @param int time: the timestamp at which the match occured in the
            sample MIDI file
        @rtype: None
        """
        self._sample_times.append(time)

def main():
    
    load_settings()

    hash_functions = {
        "0": hash_time_diff,
        "1": hash_time_diff_percentile
    }

    if len(argv) != 2 or int(argv[1]) not in range(len(hash_functions)):
        print "usage: pitches.py <int in range(" + str(len(hash_functions)) + ")>"
        return

    features = LastUpdatedOrderedDict()

    # build hashes
    for f in range(1, FAN_FACTOR):   

        hash_file = 'pitches_hash{}-{}.p'.format(argv[1], f)
        hash_file_path = 'pickles/' + hash_file

        if hash_file not in listdir('pickles'):
            training_hashes = {}
            for genre in GENRES:
                for training_file in listdir('midi-' + genre):
                    if not training_file.startswith('.'):
                        file_name = 'midi-' + genre + '/' + training_file
                        print "building hashes for {} with setting {}".format(file_name, f)
                        build_hash_table(training_file, training_hashes, genre,
                            hash_functions[argv[1]], f)

            pickle.dump(training_hashes, open(hash_file_path, "wb"))

        else:
            training_hashes = pickle.load(open(hash_file_path, "rb"))

    for f in range(1, FAN_FACTOR):
        for genre in GENRES:
            for sample_file in listdir('midi-' + genre):
                if not sample_file.startswith('.'):
                    print "classifying {} with setting {}".format(sample_file, f)
                    sample_hashes = {}
                    build_hash_table(sample_file, sample_hashes, genre,
                        hash_functions[argv[1]], f)

                    buckets, genres = match(training_hashes, sample_hashes)
                    score = get_classical(genres)
                    features.setdefault(sample_file, []).append(score)
                    # plot_graph(buckets)

    pprint (features)
    export_table(features, PITCH_FEATURES)

def build_hash_table(file, hashes, genre, hash_function, fan_factor):
    """
    Build a dictionary of peak frequency hashes as keys and their
    corresponding time onsets as values, based off MIDI files in the
    given directory of a certain genre.

    @param str directory: the name of the directory
    @param dict(int: PeakPair) hashes: the peak pair database
    @param str genre: the genre of this MIDI file
    @param function hash_function: the hash function to be used for dictionary
    keys
    @rtype: None
    """
    if genre != 'sample':
        file_name = 'midi-' + genre + '/' + file
    else:
        file_name = 'test-set/' + file

    midi = MIDIFile.from_file(file_name)
    notes = midi.notes(unit='ticks')
    peak = get_most_frequent_note(notes[:,PITCH])

    most_frequent = []
    for note in notes:
        # only consider peak pitches
        if note[PITCH] == peak:
            if len(most_frequent) > 0:
                # don't add a duplicate (considering onset)
                if most_frequent[-1][ONSET] != note[ONSET]:
                    most_frequent.append(note)
            else:
                most_frequent.append(note)

    # generate hashes for these peak pitches
    hash_function(file, genre, hashes, most_frequent, fan_factor)

def match(training, sample):
    """
    Return all buckets representing hash matches between the sample MIDI file
    and each individual training MIDI file (one per bucket). Also return a
    tally of matches according to genres.

    @param dict(int: PeakPair) training: the peak pair database
    @param dict(int: PeakPair) sample: the peak pairs of the sample MIDI file
    @rtype: dict(str: Bucket), dict(str: int)
    """
    buckets = {}
    genres = {}

    for key, value in sample.items():
        if key in training:
            for sample_time in value:
                for training_time in training[key]:
                    # check sample is not matching on itself
                    # if sample_time.file_name != training_time.file_name:
                    bucket_name = training_time.file_name
                    if key in training:
                        if bucket_name not in buckets:
                            # make a new bucket for this track (use track name)
                            buckets[bucket_name] = Bucket()

                        buckets[bucket_name].add_training_time(training_time.onset)
                        buckets[bucket_name].add_sample_time(sample_time.onset)
                        genres[training_time.genre] = genres.get(training_time.genre, 0) + 1

    return buckets, genres

def get_most_frequent_note(pitches):
    """
    Return the MIDI pitch (from 0 to 127) that occurs the most often in the
    pitches of a MIDI file.

    @param list[int] pitches: a list of MIDI pitches
    @rtype int
    """
    tally = {}
    for pitch in pitches:
        note = Note(int(pitch))
        tally[note] = tally.get(note, 0) + 1
    most_frequent = nlargest(TOP_MOST_FREQUENT, tally, key=tally.get)

    return most_frequent[0].midi_pitch

def hash_time_diff(file, genre, hashes, notes):
    """
    Add or append to the hashes dictionary with a hash that considers the
    difference between peak pair's timestamps. Store the hash along with the
    associate file name and genre.

    @param str file: the name of the file
    @param str genre: the genre of the file
    @param dict(int: PeakPair) hashes: the peak pair database
    @param list[int] notes: a list of MIDI notes in the madmom library format
    @rtype: None
    """
    for i in range(len(notes) - (FAN_FACTOR + 1)):
        for j in range(1, FAN_FACTOR + 1):

            # hash = later offset - earlier offset
            h = notes[i+j][ONSET] - notes[i][ONSET]
            pair = PeakPair(notes[i][ONSET], file, genre)
            hashes.setdefault(h, []).append(pair)

def hash_time_diff_percentile(file, genre, hashes, notes):
    """
    Add or append to the hashes dictionary with a hash that considers the
    difference between peak pair's timestamps and where it occurs in the file
    as a percentile. Store the hash along with the associate file name and
    genre.

    @param str file: the name of the file
    @param str genre: the genre of the file
    @param dict(int: PeakPair) hashes: the peak pair database
    @param list[int] notes: a list of MIDI notes in the madmom library format
    @rtype: None
    """
    total_length = notes[-1][ONSET]
    for i in range(len(notes) - (FAN_FACTOR + 1)):
        for j in range(1, FAN_FACTOR + 1):

            # hash is of the form onset_diff|percentile
            # ex: diff = 20, percentile = 50, hash = 2050
            percentile = notes[i][ONSET] / float(total_length) * 100
            h = (notes[i+j][ONSET] - notes[i][ONSET]) * 100 + int(percentile)
            pair = PeakPair(notes[i][ONSET], file, genre)
            hashes.setdefault(h, []).append(pair)

def hash_time_diff_pitch(file, genre, hashes, notes):
    for i in range(len(notes) - (FAN_FACTOR + 1)):
        for j in range(1, FAN_FACTOR + 1):
            h = notes[i+j][ONSET] - notes[i][ONSET] * 1000 + notes[i][PITCH]
            pair = PeakPair(notes[i][ONSET], file, genre)
            hashes.setdefault(h, []).append(pair)

def hash_time_diff_pitch_percentile(file, genre, hashes, notes):
    for i in range(len(notes) - (FAN_FACTOR + 1)):
        for j in range(1, FAN_FACTOR + 1):
            percentile = notes[i][PITCH] / 127.0 * 10
            h = notes[i+j][ONSET] - notes[i][ONSET] * 10 + int(percentile)
            pair = PeakPair(notes[i][ONSET], file, genre)
            hashes.setdefault(h, []).append(pair)

def plot_graph(buckets):
    """
    Plot the matches in each bucket, with the timestamps of where the match
    occurs in the training MIDI file for the x axis, and the timestamps of
    where the match occurs in the sample MIDI file for the y axis.

    @param dict(str: Bucket) buckets: a collection of buckets that contain
        matches for sample MIDI file
    @rtype: None
    """
    for key, value in buckets.items():
        plt.plot(
            value.get_training_times(),
            value.get_sample_times(),
            'ro')
        plt.title(key)
        plt.xlabel('training')
        plt.ylabel('sample')
        # plt.show()
        plt.savefig('graphs/' + key + '.png')
        plt.close()

if __name__ == '__main__':
    main()
