import numpy as np

from warnings import filterwarnings
from madmom.utils.midi import *
from collections import OrderedDict

ONSET = 0
PITCH = 1
DURATION = 2
VELOCITY = 3
CHANNEL = 4

FAN_FACTOR = 5
# MELODY_FEATURES = 5

GENRES = ['classical', 'rock']
SEPARATOR = ','
MELODY_FEATURES = 'features/melody_features.csv'
PITCH_FEATURES = 'features/pitch_features.csv'
LABELS_FILE = 'labels.csv'
TEST_FILE = 'test.csv'
TEST_LABELS_FILE = 'test-labels.csv'

# https://docs.python.org/2/library/collections.html#collections.OrderedDict
class LastUpdatedOrderedDict(OrderedDict):
    'Store items in the order the keys were last added'

    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        OrderedDict.__setitem__(self, key, value)

def load_settings():
    filterwarnings('ignore')
    np.set_printoptions(suppress=True)
    np.set_printoptions(threshold=np.nan)
    np.set_printoptions(edgeitems=10)

def get_classical(genres):
    if not genres or 'classical' not in genres:
        return 0
    if 'rock' not in genres:
        return 1
    total = genres['classical'] + genres['rock']
    return genres['classical'] / float(total)

def get_ticks_per_bar(midi, file):
    notes = midi.notes(unit='ticks')
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

def find_event(events, event_type):
    for i in range(len(events)):
        if isinstance(events[i], event_type):
            return i
    return None

def get_notes(file):
    midi = MIDIFile.from_file(file)
    return midi.notes(unit='ticks')

def export_table(table, csv):
    file = open(csv, 'w')
    for value_list in table.values():
        row = SEPARATOR.join(map(str, value_list)) + '\n'
        file.write(row)
