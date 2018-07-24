#!/usr/bin/python2

import numpy as np
from scipy import signal
from binascii import unhexlify

def load_one(filename):
    with open(filename, "r") as f:
        value = f.readline()

    return [ord(c) for c in value.decode('hex')]

def load_all(filename, number=0):
    with open(filename, "r") as f:
        if number == 0:
            data = f.read()
        else:
            data = ''
            for i in range(0, number):
                data += f.readline()

    return [[ord(c) for c in line.decode('hex')]
            for line in data.split('\n')]

def load_traces(filename,number,wstart=0,wend=0):
    # load raw
    traces = []
    for i in range(number):
        # open file
        trace = np.load("%s_%d.npy"%(filename,i))
        if trace is None:
            print("ERROR null trace")
            sys.exit()
        traces.append(np.absolute(trace))
    
    # align
    aligned = []
    target = None
    for trace in traces:
        if target is None:
            target = trace
        else:
            shift = (np.argmax(signal.correlate(trace,
                    target)) - (len(target)-1))
            if(shift >= 0):
                trace[0:len(trace)-shift-1] = trace[shift:len(trace)-1]
                trace[len(trace)-shift+1:len(trace)-1] = 0
            else:
                trace[0:len(trace)-1+shift] = trace[0:len(trace)-1+shift]
                trace[len(trace)+shift+1:len(trace)-1] = 0
    
        if(wstart!=wend):
            trace = trace[wstart:wend]
        aligned.append(trace)
    
    return np.asarray(aligned)

if __name__ == "__main__":
    pass
