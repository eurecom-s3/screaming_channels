#!/usr/bin/python2
# The collection script has to use Python 2 for GNUradio, so keep using it here.

import click
import numpy as np
from matplotlib import pyplot as plt
import os
from os import path
from scipy.stats import multivariate_normal
import pickle
import itertools
import binascii

from load import load_all,load_one,load_traces


# Configuration that applies to all attacks; set by the script entry point (cli()).
PLOT = None
NUM_KEY_BYTES = None
BRUTEFORCE = None
PLAINTEXTS = None
TRACES = None
KEYFILE = None


@click.group()
@click.option("--data-path", type=click.Path(exists=True, file_okay=False),
              help="Directory where the traces are stored.")
@click.option("--name", default="",
              help="Identifier of the experiment (obsolete; only for compatibility).")
@click.option("--num-traces", default=0, show_default=True,
              help="The number of traces to use, or 0 to use the maximum available.")
@click.option("--start-point", default=0, show_default=True,
              help="Index of the first point in each trace to use.")
@click.option("--end-point", default=0, show_default=True,
              help="Index of the last point in each trace to use, or 0 for the maximum.")
@click.option("--plot/--no-plot", default=False, show_default=True,
              help="Visualize relevant data (use only with a small number of traces.")
@click.option("--num-key-bytes", default=16, show_default=True,
              help="Number of bytes in the key to attack.")
@click.option("--bruteforce/--no-bruteforce", default=False, show_default=True,
              help="Attempt to fix a few wrong key bits with informed exhaustive search.")
def cli(data_path, num_traces, start_point, end_point, plot, num_key_bytes,
        bruteforce, name):
    """
    Run an attack against previously collected traces.

    Each attack is a separate subcommand. The options to the top-level command
    apply to all attacks; see the individual attacks' documentation for
    attack-specific options.
    """
    global PLOT, NUM_KEY_BYTES, BRUTEFORCE, PLAINTEXTS, TRACES, KEYFILE
    PLOT = plot
    NUM_KEY_BYTES = num_key_bytes
    BRUTEFORCE = bruteforce
    PLAINTEXTS = load_all(path.join(data_path, 'pt_%s.txt' % name))
    TRACES = load_traces(path.join(data_path, 'avg_%s' % name),
                         num_traces or len(PLAINTEXTS),
                         start_point, end_point)
    KEYFILE = path.join(data_path, 'key_%s.txt' % name)


### UTILS ###

def cov(x, y):
    # Find the covariance between two 1D lists (x and y).
    # Note that var(x) = cov(x, x)
    return np.cov(x, y)[0][1]
 
hw = [bin(n).count("1") for n in range(256)]

sbox=(
0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16)

def intermediate(pt, keyguess):
    # tmp = pt ^ keyguess
    # return sbox[tmp] ^ tmp
    return sbox[pt ^ keyguess]

def print_result(bestguess,knownkey,pge):
    print "Best Key Guess: ",
    for b in bestguess: print " %02x "%b,
    print ""
    
    print "Known Key:      ",
    for b in knownkey: print " %02x "%b,
    print ""
    
    print "PGE:            ",
    for b in pge: print "%03d "%b,
    print ""

    print "SUCCESS:        ",
    tot = 0
    for g,r in zip(bestguess,knownkey):
        if(g==r):
            print "  1 ",
            tot += 1
        else:
            print "  0 ",
    print ""
    print "NUMBER OF CORRECT BYTES: %d"%tot


### ATTACKS ###

@cli.command()
@click.argument("template_dir", type=click.Path(file_okay=False, writable=True))
@click.option("--num-pois", default=2, show_default=True,
              help="Number of points of interest.")
@click.option("--poi-spacing", default=5, show_default=True,
              help="Minimum number of points between two points of interest.")
def tra_create(template_dir, num_pois, poi_spacing):
    """
    Template Radio Analysis; create a template.

    The data set should have a considerable size in order to allow for the
    construction of an accurate model. In general, the more data is used for
    template creation the less is needed to apply the template.

    The template directory is where we store multiple files comprising the
    template; beware that existing files will be overwritten!
    """
    try:
        os.makedirs(template_dir)
    except OSError:
        # Checking the directory before attempting to create it leads to race
        # conditions.
        if not path.isdir(template_dir):
            raise

    if PLOT:
        plt.plot(np.average(TRACES,axis=0),'b')
        plt.show()

    tempKey = load_all(KEYFILE)
    fixed_key = (np.shape(tempKey)[0] == 1)
 
    for knum in range(NUM_KEY_BYTES):
        if(fixed_key):
            tempSbox = [sbox[PLAINTEXTS[i][knum] ^ tempKey[0][knum]] for i in range(len(TRACES))]
        else:
            tempSbox = [sbox[PLAINTEXTS[i][knum] ^ tempKey[i][knum]] for i in range(len(TRACES))]

        tempHW = [hw[s] for s in tempSbox]
        
        # Sort traces by HW
        # Make 9 blank lists - one for each Hamming weight
        tempTracesHW = [[] for _ in range(9)]
        
        # Fill them up
        for i, trace in enumerate(TRACES):
            HW = tempHW[i]
            tempTracesHW[HW].append(trace)

        # Check to have at least a trace for each HW
        for HW in range(9):
            assert len(tempTracesHW[HW]) != 0, "No trace with HW = %d, try increasing the number of traces" % HW

        # Switch to numpy arrays
        tempTracesHW = [np.array(tempTracesHW[HW]) for HW in range(9)]

        # Find averages
        tempMeans = np.zeros((9, len(TRACES[0])))
        for i in range(9):
            tempMeans[i] = np.average(tempTracesHW[i], 0)

        # Find sum of differences
        tempSumDiff = np.zeros(len(TRACES[0]))
        for i in range(9):
            for j in range(i):
                tempSumDiff += np.abs(tempMeans[i] - tempMeans[j])
        
        if PLOT:
            plt.plot(tempSumDiff,label="subkey %d"%knum)
            plt.legend()

        # Find POIs
        POIs = []
        for i in range(num_pois):
            # Find the max
            nextPOI = tempSumDiff.argmax()
            POIs.append(nextPOI)
            
            # Make sure we don't pick a nearby value
            poiMin = max(0, nextPOI - poi_spacing)
            poiMax = min(nextPOI + poi_spacing, len(tempSumDiff))
            for j in range(poiMin, poiMax):
                tempSumDiff[j] = 0

        # Fill up mean and covariance matrix for each HW
        meanMatrix = np.zeros((9, num_pois))
        covMatrix  = np.zeros((9, num_pois, num_pois))
        for HW in range(9):
            for i in range(num_pois):
                # Fill in mean
                meanMatrix[HW][i] = tempMeans[HW][POIs[i]]
                for j in range(num_pois):
                    x = tempTracesHW[HW][:,POIs[i]]
                    y = tempTracesHW[HW][:,POIs[j]]
                    covMatrix[HW,i,j] = cov(x, y)

        with open(path.join(template_dir, 'POIs_%d' % knum), 'wb') as fp:
            pickle.dump(POIs, fp)
        with open(path.join(template_dir, 'covMatrix_%d' % knum), 'wb') as fp:
            pickle.dump(covMatrix, fp)
        with open(path.join(template_dir, 'meanMatrix_%d' % knum), 'wb') as fp:
            pickle.dump(meanMatrix, fp)

    if PLOT:
        plt.show()
    

@cli.command()
@click.argument("template_dir", type=click.Path(exists=True, file_okay=False))
def tra_attack(template_dir):
    """
    Template Radio Analysis; apply a template.

    Use the template to attack the key in a new data set (i.e. different from
    the one used to create the template). The template directory must be the
    location of a previously created template with compatible settings (e.g.
    same trace length).
    """
    if PLOT:
        plt.plot(np.average(TRACES,axis=0),'b')
        plt.show()
    
    atkKey = load_one(KEYFILE)
    
    scores = []
    bestguess = [0]*16
    pge = [256]*16

    for knum in range(0,NUM_KEY_BYTES):
        with open(path.join(template_dir, 'POIs_%d' % knum), 'rb') as fp:
            POIs = pickle.load(fp)
        with open(path.join(template_dir, 'covMatrix_%d' % knum), 'rb') as fp:
            covMatrix = pickle.load(fp)
        with open(path.join(template_dir, 'meanMatrix_%d' % knum), 'rb') as fp:
            meanMatrix = pickle.load(fp)

        # Ring buffer for keeping track of the last N best guesses
        window = [None] * 10
        window_index = 0
        
        # Running total of log P_k
        P_k = np.zeros(256)
        for j, trace in enumerate(TRACES):
            # Grab key points and put them in a small matrix
            a = [trace[poi] for poi in POIs]
            
            # Test each key
            for k in range(256):
                # Find HW coming out of sbox
                HW = hw[sbox[PLAINTEXTS[j][knum] ^ k]]
            
                # Find p_{k,j}
                rv = multivariate_normal(meanMatrix[HW], covMatrix[HW])
                p_kj = rv.pdf(a)
           
                # Add it to running total
                P_k[k] += np.log(p_kj)

            window[window_index] = P_k.argsort()[-1]
            window_index = (window_index + 1) % len(window)

            if all(k == atkKey[knum] for k in window):
                print "subkey %d found with %d traces" % (knum, j)
                break
        else:
            print "subkey %d NOT found" % knum

        bestguess[knum] = P_k.argsort()[-1]
        pge[knum] = list(P_k.argsort()[::-1]).index(atkKey[knum])
        scores.append(P_k)
   
    print_result(bestguess, atkKey, pge)
    if BRUTEFORCE:
        brute_force_bitflip(bestguess, atkKey)

@cli.command()
def cra():
    """
    Correlation Radio Analysis.

    Run a "standard" correlation attack against a data set, trying to recover
    the key used for the observed AES operations. The attack works by
    correlating the amplitude-modulated signal of the screaming channel with the
    power consumption of the SubBytes step in the first round of AES, using a
    Hamming-weight model.
    """
    if PLOT:
        for t in TRACES:
            plt.plot(t)
        avg = np.average(TRACES, axis=0)
        plt.plot(avg, 'b')
        # np.save("tpl_template.npy",avg)
        plt.show()

        # 4: Find sum of differences
        tempSumDiff = np.zeros(np.shape(TRACES)[1])
        for i in range(np.shape(TRACES)[0]-1-5):
            for j in range(i, i+5):
                tempSumDiff += np.abs(TRACES[i] - TRACES[j])
        plt.plot(tempSumDiff)
        plt.show()
    
    knownkey = load_one(KEYFILE)
    numtraces = np.shape(TRACES)[0]-1
    numpoint = np.shape(TRACES)[1]
    
    bestguess = [0]*16
    pge = [256]*16

    stored_cpas = []

    for bnum in range(NUM_KEY_BYTES):
        cpaoutput = [0]*256
        maxcpa = [0]*256
        for kguess in range(256):
            print "Subkey %2d, hyp = %02x: "%(bnum, kguess),

            #Initialize arrays and variables to zero
            sumnum = np.zeros(numpoint)
            sumden1 = np.zeros(numpoint)
            sumden2 = np.zeros(numpoint)
    
            hyp = np.zeros(numtraces)
            for tnum in range(numtraces):
                hyp[tnum] = hw[intermediate(PLAINTEXTS[tnum][bnum], kguess)]

            #Mean of hypothesis
            meanh = np.mean(hyp, dtype=np.float64)
    
            #Mean of all points in trace
            meant = np.mean(TRACES, axis=0, dtype=np.float64)
    
            for tnum in range(numtraces):
                hdiff = (hyp[tnum] - meanh)
                tdiff = TRACES[tnum, :] - meant
    
                sumnum = sumnum + (hdiff*tdiff)
                sumden1 = sumden1 + hdiff*hdiff 
                sumden2 = sumden2 + tdiff*tdiff
    
            cpaoutput[kguess] = sumnum / np.sqrt(sumden1 * sumden2)
            maxcpa[kguess] = max(abs(cpaoutput[kguess]))
    
            print maxcpa[kguess]
    
        bestguess[bnum] = np.argmax(maxcpa)
    
        cparefs = np.argsort(maxcpa)[::-1]
    
        #Find PGE
        pge[bnum] = list(cparefs).index(knownkey[bnum])
        stored_cpas.append(maxcpa)
    
    print_result(bestguess, knownkey, pge)
    if BRUTEFORCE:
        brute_force(stored_cpas, knownkey)

def brute_force_bitflip(startkey, knownkey, n_bits=6):
    knownkey = int(binascii.hexlify(bytearray(knownkey)), 16)
    startkey = int(binascii.hexlify(bytearray(startkey)), 16)

    print "Starting bit-flip  bruteforce: nbytes = %d" % (n_bits)

    i = 0
    for i in range(1, n_bits+1):
        print "Flipping %d bits" % i
        bit_masks = itertools.combinations([1<<j for j in range(127)], r=i)
    
        for masks in bit_masks:
            tmp_key = startkey
            for mask in masks:
                tmp_key ^= mask

            i += 1
            if tmp_key == knownkey:
                print "Bruteforce succeeded in %d guesses" % i
                return

    print "Bruteforce failed"
    import IPython; IPython.embed()


def brute_force(scores, knownkey, num_bytes=4, n_scores=128):
    """
    This implements a simple last-stage brute-force attack.
    It tries to bruteforce the num_bytes unlikeliest bytes of the keys,
    based on scores.
    For each of this bytes, it tries the best n_scores guesses
    """
    print "Individual score[0]-score[1] for key bytes:"
    diverging = []
    for i, byte_scores in zip(range(16), scores):
        sorted_scores = sorted(byte_scores, reverse=True)
        d = sorted_scores[0] - sorted_scores[1]
        print i, d
        diverging.append(d)

    print "Starting bruteforce: nbytes = %d, n_scores = %d" % (num_bytes,
                                                                 n_scores)

    # Set up the attack based on the params
    attack_bytes = np.argsort(diverging)[:num_bytes]
    attack_list = []
    for i in range(16):
        if i in attack_bytes:
            attack_list.append(np.argsort(scores[i])[::-1][:n_scores])
        else:
            attack_list.append([np.argmax(scores[i])])
    
    print "Attacking keybytes: ", attack_bytes

    i = 0
    for guess in itertools.product(*attack_list):
        i += 1
        if list(guess) == knownkey:
            print "Bruteforce succeeded in %d guesses" % i
            return

    print "Bruteforce failed"
    import IPython; IPython.embed()


if __name__ == "__main__":
    cli()
