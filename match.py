# import numpy as np
import sys
import pickle
import pprint
import warnings

from madmom.utils.midi import *
from os import listdir
from populate import *

TABLE_FILE = 'table.csv'
TALLY = {}

def main():
    warnings.filterwarnings('ignore')

    master_table = pickle.load(open("table.p", "rb"))

    for file in listdir('test-set'):
        if not file.startswith('.'):
            # table = {}
            # midi_train(table, 'test-set/' + file)
            # match(file, table, master_table)

    pprint.pprint(TALLY)
    
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
