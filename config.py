from madmom.utils.midi import *

ONSET = 0
PITCH = 1
DURATION = 2
VELOCITY = 3
CHANNEL = 4

FAN_FACTOR = 5

GENRES = ['classical', 'rock']

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
