import numpy as np
import sys
import pickle
import pprint

from madmom.utils.midi import *
from populate import *

TABLE_FILE = 'table.csv'
TABLE = {}
TALLY = {}

def main():
    midi_train(TABLE, str(sys.argv[1]))
    match(pickle.load(open("table.p", "rb")))
    
def match(master_table):
    for tick, trial_pair in TABLE.items():
        if tick in master_table.keys():
            for master_pair in master_table[tick]:
                if trial_pair[0][0] == master_pair[0]:
                    record_match(trial_pair[0][1])
    
    print TALLY
    guess = max(TALLY, key=TALLY.get)
    print 'is this {}?'.format(guess)

def record_match(file):
    if file not in TALLY.keys():
        TALLY[file] = 1
    else:
        TALLY[file] += 1

if __name__ == '__main__':
    main()
