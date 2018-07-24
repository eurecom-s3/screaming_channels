import sys
import numpy as np
import struct

from binascii import unhexlify
from os import chdir, getcwd
from os.path import isfile, abspath

from load import load_traces, load_all

def main(trace_directory, trace_name, number):
    trace_directory = abspath(trace_directory)
    ptfile = '%s/pt_%s.txt' % (trace_directory, trace_name)

    pt_data = load_all(ptfile, number=number)[:-1]
    textin = np.array(pt_data)
    traces = load_traces('%s/avg_%s' % (trace_directory, trace_name), number)

    assert traces.shape[0] == textin.shape[0]

    with open('tracefile', 'wb') as f:
        for t in traces.flatten():
            f.write(struct.pack('f', t))

    with open('plaintext', 'wb') as f:
        for t in textin.flatten():
            f.write(struct.pack('B', t))

    print("Add following to CONFIG:\n")
    print("[Traces]")
    print("files=1")
    print("trace_type=f")
    print("transpose=true")
    print("index=0")
    print("nsamples=%d"% traces.shape[1])
    print("trace=tracefile %d %d"%(traces.shape[0], traces.shape[1]))
    print("")
    print("[Guesses]")
    print("files=1")
    print("guess_type=u")
    print("transpose=true")
    print("guess=plaintext %d %d"%(textin.shape[0], textin.shape[1]))




if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 %s TRACEDIR NAMEPATTERN [NUMBER]" % __file__)
        exit(-1)
    stop_trace = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    main(sys.argv[1], sys.argv[2], stop_trace)
