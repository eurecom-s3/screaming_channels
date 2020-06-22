#!/usr/bin/python2

import numpy as np
# from scipy import signal
from binascii import unhexlify
from os import path
from scipy import stats

# Load all plaintexts and key(s) from the respective files
def load_all(filename, number=0):
    with open(filename, "r") as f:
        if number == 0:
            data = f.read()
        else:
            data = ''
            for i in range(0, number):
                data += f.readline()
            if data[len(data)-1] == '\n':
                 data = data[0:len(data)-1]
    return [[ord(c) for c in line.decode('hex')]
            for line in data.split('\n')]

# Per-trace pre-processing:
# 1. z-score normalization
def pre_process(trace, norm):
    if norm:
        mu = np.average(trace)
        std = np.std(trace)
        if std != 0:
            trace = (trace - mu) / std
    return trace
 
# Smart loading of the traces from files
# 1. Discard empty traces (errors occurred during collection)
# 1. Apply pre-processing techniques
# 2. Keep all the traces in a batch or average them (if they were collected with
#    the keep-all option. 
def generic_load(data_path,name,number,wstart=0,wend=0, average=True,
        norm=False, norm2=False, mimo=""):
    """
    Function that loads plainext, key(s), and (raw) traces.
    """

    empty = 0
    p = load_all(path.join(data_path, 'pt_%s.txt' % name), number)
    k = load_all(path.join(data_path, 'key_%s.txt' % name), number)
    fixed_key = False
    if len(k) == 1:
        fixed_key = True
    
    fixed_plaintext = False
    if len(p) == 1:
        fixed_plaintext = True

    plaintexts = []
    keys = []
    traces = []

    if mimo != "":
        name = name + "_" + mimo
 
    for i in range(number):
        # read average or raw traces from file
        raw_traces = np.load(
                path.join(data_path, 'avg_%s_%d.npy' % (name, i))
        )

        if np.shape(raw_traces) == () or not raw_traces.any():
            # print "empty trace", empty
            empty += 1
            continue

        # if average, transform into array with one element
        # if len(np.shape(raw_traces)) == 1:
        raw_traces = [raw_traces]

        if wend != 0:
            raw_traces = np.asarray(raw_traces)[:,wstart:wend]

        if average:
            # if raw_traces[0].all() == 0:
                # continue
            # print type(raw_traces)
            avg = np.average(raw_traces, axis=0)
            avg = pre_process(avg, norm)
            traces.append(avg)
            if fixed_plaintext:
                plaintexts.append(p[0])
            else:
                plaintexts.append(p[i])
            if fixed_key:
                keys.append(k[0])
            else:
                keys.append(k[i])
        else:
            # iterate over traces
            for trace in raw_traces:
                if trace.all() == 0:
                    continue
                trace = pre_process(trace, norm)
                traces.append(trace)
                plaintexts.append(p[i])
                if fixed_key:
                    keys.append(k[0])
                else:
                    keys.append(k[i])
    
    traces = np.asarray(traces)

    # Apply z-score normalization on the set
    if norm2:
        mu = np.average(traces, axis=0)
        std = np.std(traces, axis=0)
        traces = (traces - mu) / std

    return fixed_key, plaintexts, keys, traces

if __name__ == "__main__":
    pass
