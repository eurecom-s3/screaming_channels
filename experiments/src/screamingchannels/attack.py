#!/usr/bin/python2
# The collection script has to use Python 2 for GNUradio, so keep using it here.

import click
import numpy as np
from matplotlib import pyplot as plt

SMALL_SIZE = 8*4
MEDIUM_SIZE = 10*4
BIGGER_SIZE = 12*4

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

import os
from os import path
from scipy.stats import multivariate_normal, linregress, norm, pearsonr, entropy
from scipy.stats import ttest_ind, f
from scipy import signal
import pickle
import itertools
import binascii
import math
import statsmodels.api as sm
from sklearn.feature_selection import mutual_info_classif

from load import generic_load


# Configuration that applies to all attacks; set by the script entry point (cli()).
# Plus other global variables
PLOT = None
SAVE_IMAGES = None
NUM_KEY_BYTES = None
BRUTEFORCE = None
BIT_BOUND_END = None
PLAINTEXTS = None
KEYS = None
CIPHERTEXTS = None
FIXED_KEY = None
FIXED_PLAINTEXT = None
TRACES = None
KEYFILE = None
VARIABLES = None
VARIABLE_FUNC = None
CLASSES = None
SETS = None
MEANS = None
MEANS_TEST = None
MEANS_PROFILE = None
VARS = None
STDS = None
SNRS = None
TTESTS = None
PTTESTS = None
CORRS = None
SOADS = None
RS = None
RZS = None
PS = None
POIS = None
TRACES_REDUCED = None
TRACES_TEST = None
TRACES_PROFILE = None
PROFILE_RS = None
PROFILE_RZS = None
PROFILE_MEANS = None
PROFILE_COVS = None
PROFILE_STDS = None
PROFILE_MEAN_TRACE = None
LOG_PROBA = None

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
@click.option("--save-images/--no-save-images", default=False, show_default=True,
              help="Save images (when implemented).")
@click.option("--wait/--no-wait", default=False, show_default=True,
              help="Wait for user input after having loaded the traces.")
@click.option("--num-key-bytes", default=16, show_default=True,
              help="Number of bytes in the key to attack.")
@click.option("--bruteforce/--no-bruteforce", default=False, show_default=True,
              help="Attempt to fix a few wrong key bits with informed exhaustive search.")
@click.option("--bit-bound-end", default=40, show_default=True,
              help="Set upper bound to key rank when bruteforcing.")
@click.option("--average/--no-average", default=True, show_default=True,
              help="Use average of a batch as preprocessing.")
@click.option("--norm/--no-norm", default=False, show_default=True,
              help="Normalize each trace individually: x = (x-avg(x))/std(x).")
@click.option("--norm2/--no-norm2", default=False, show_default=True,
              help="Normalize each trace set: traces = (traces-avg(traces))/std(traces).")
@click.option("--mimo", default="",
              help="Choose ch1, ch2, eg, or mr")
def cli(data_path, num_traces, start_point, end_point, plot, save_images, wait, num_key_bytes,
        bruteforce, bit_bound_end, name, average, norm, norm2, mimo):
    """
    Run an attack against previously collected traces.

    Each attack is a separate subcommand. The options to the top-level command
    apply to all attacks; see the individual attacks' documentation for
    attack-specific options.
    """
    global PLOT, WAIT, NUM_KEY_BYTES, BRUTEFORCE, BIT_BOUND_END, PLAINTEXTS, TRACES, KEYFILE, DATAPATH
    global KEYS, FIXED_KEY, SAVE_IMAGES, CIPHERTEXTS
    SAVE_IMAGES = save_images
    PLOT = plot
    WAIT = wait
    NUM_KEY_BYTES = num_key_bytes
    if bruteforce and num_key_bytes != 16:
        raise Exception("Bruteforce not available for num_key_bytes != 16")
    BRUTEFORCE = bruteforce
    BIT_BOUND_END = bit_bound_end
    KEYFILE = path.join(data_path, 'key_%s.txt' % name)
    DATAPATH = data_path
    
    FIXED_KEY, PLAINTEXTS, KEYS, TRACES = generic_load(data_path, name, num_traces,
            start_point, end_point, average, norm, norm2, mimo)
    
    CIPHERTEXTS = map(aes, PLAINTEXTS, KEYS)

    variable_func = None
    PLAINTEXTS = np.asarray(PLAINTEXTS)
    KEYS = np.asarray(KEYS)
    CIPHERTEXTS = np.asarray(CIPHERTEXTS)

### CCS18 UTILS (from ChipWhisper) ###

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

### CHES20 UTILS ###

# Compute the leak variable starting from the plaintext and key
def compute_variables(variable):
    global VARIABLES, CLASSES, VARIABLE_FUNC, FIXED_PLAINTEXT
    VARIABLES = np.zeros((NUM_KEY_BYTES, len(TRACES)), dtype=int)
    FIXED_PLAINTEXT = False
    if variable == "hw_sbox_out":
        CLASSES = range(0, 9)
        VARIABLE_FUNC = lambda p, k : hw[sbox[p ^ k]]
    elif variable == "hw_p_xor_k":
        CLASSES = range(0, 9)
        VARIABLE_FUNC = lambda p, k : hw[p ^ k]
    elif variable == "sbox_out":
        CLASSES = range(0, 256)
        VARIABLE_FUNC = lambda p, k : sbox[p ^ k]
    elif variable == "p_xor_k":
        CLASSES = range(0, 256)
        VARIABLE_FUNC = lambda p, k : p ^ k
    elif variable == "p":
        CLASSES = range(0, 256)
        VARIABLE_FUNC = lambda p, k : p
        FIXED_PLAINTEXT = True
    elif variable == "hw_p":
        CLASSES = range(0, 9)
        VARIABLE_FUNC = lambda p, k : hw[p]
        FIXED_PLAINTEXT = True
    elif variable == "hw_k":
        CLASSES = range(0, 9)
        VARIABLE_FUNC = lambda p, k : hw[k]
    elif variable == "k":
        CLASSES = range(0, 256)
        VARIABLE_FUNC = lambda p, k : k
    elif variable == "hw_k":
        CLASSES = range(0, 9)
        VARIABLE_FUNC = lambda p, k : hw[k]
    elif variable == "hd":
        CLASSES = range(0, 7)
        VARIABLE_FUNC = lambda p, k : hw[(p ^ k) ^ sbox[p ^ k]] - 1
    elif variable == "fixed_vs_fixed":
        CLASSES = range(0, 2)
        VARIABLE_FUNC = lambda p, k: 1 if p ^ k == 48 else 0
    elif variable == "c":
        CLASSES = range(0, 256)
    elif variable == "hw_c":
        CLASSES = range(0, 9)
    else:
        raise Exception("Variable type %s is not supported" % variable)

    if variable == "c":
        for bnum in range(NUM_KEY_BYTES):
            VARIABLES[bnum] = CIPHERTEXTS[:,bnum]
    elif variable == "hw_c":
        for bnum in range(NUM_KEY_BYTES):
            VARIABLES[bnum] = [hw[c] for c in CIPHERTEXTS[:,bnum]]
    else:
        for bnum in range(NUM_KEY_BYTES):
            VARIABLES[bnum] = map(VARIABLE_FUNC, PLAINTEXTS[:, bnum], KEYS[:, bnum])

# Classify the traces according to the leak variable
def classify():
    global SETS
    SETS = [[[] for _ in CLASSES] for b in range(NUM_KEY_BYTES)]
    for bnum in range(NUM_KEY_BYTES):
        for cla, trace in zip(VARIABLES[bnum], TRACES):
            SETS[bnum][cla].append(trace)

        SETS[bnum] = [np.array(SETS[bnum][cla]) for cla in CLASSES]

# Estimate mean, variance, and standard deviation for each class, and the
# average trace for all traces
def estimate():
    global MEANS, VARS, STDS
    global PROFILE_MEAN_TRACE

    PROFILE_MEAN_TRACE = np.average(TRACES, axis=0)
    MEANS = np.zeros((NUM_KEY_BYTES, len(CLASSES), len(TRACES[0])))
    VARS = np.zeros((NUM_KEY_BYTES, len(CLASSES), len(TRACES[0])))
    STDS = np.zeros((NUM_KEY_BYTES, len(CLASSES), len(TRACES[0])))
    
    for bnum in range(NUM_KEY_BYTES):
        for cla in CLASSES:
            MEANS[bnum][cla] = np.average(SETS[bnum][cla], axis=0)
            VARS[bnum][cla] = np.var(SETS[bnum][cla], axis=0)
            STDS[bnum][cla] = np.std(SETS[bnum][cla], axis=0)

# Estimate the side-channel SNR
def estimate_snr():
    global SNRS
    SNRS = np.zeros((NUM_KEY_BYTES, len(TRACES[0])))
    for bnum in range(NUM_KEY_BYTES):
        SNRS[bnum] = np.var(MEANS[bnum], axis=0) / np.average(VARS[bnum], axis=0)

# Estimate the t-test
def estimate_ttest():
    global TTESTS, PTTESTS
    TTESTS = np.zeros((NUM_KEY_BYTES, len(TRACES[0])))
    PTTESTS = np.zeros((NUM_KEY_BYTES, len(TRACES[0])))
    for bnum in range(NUM_KEY_BYTES):
        TTESTS[bnum], PTTESTS[bnum] = ttest_ind(SETS[bnum][1],
                SETS[bnum][0], axis=0, equal_var=False)
    
    tmax = np.max(np.absolute(TTESTS[0]))
    p = PTTESTS[0][np.argmax(np.absolute(TTESTS[0]))]
    print "tmax", tmax, "p", p, "p < 0.00001", p < 0.00001

# Split a set of traces into a k-folds, 1 for test and k-1 for profiling
# fold indicates which of the k-folds is the test set
def split(fold, k_fold):
    global TRACES_TEST, TRACES_PROFILE
    global VARIABLES_TEST, VARIABLES_PROFILE
    Ntraces = len(TRACES)
    Ntest = Ntraces / k_fold
    Nprofiling = Ntraces - Ntest
 
    test_range = [i for i in range(0,Ntraces) if i >= fold*Ntest 
            and i < fold*Ntest + Ntest]
    profiling_range = [i for i in range(0,Ntraces) if i < fold*Ntest 
            or i >= fold*Ntest + Ntest]

    TRACES_TEST = TRACES[test_range]
    TRACES_PROFILE = TRACES[profiling_range]

    VARIABLES_TEST = VARIABLES[:, test_range]
    VARIABLES_PROFILE = VARIABLES[:, profiling_range]

# Classify the profiling set based on the leak variable and estimate the
# average of each class
def classify_and_estimate_profile():
    global MEANS_PROFILE
    MEANS_PROFILE = np.zeros((NUM_KEY_BYTES, len(CLASSES), len(TRACES[0])))
    sets = [[[] for _ in CLASSES] for b in range(NUM_KEY_BYTES)]
    for bnum in range(NUM_KEY_BYTES):
        for cla, trace in zip(VARIABLES_PROFILE[bnum], TRACES_PROFILE):
            sets[bnum][cla].append(trace)

        sets[bnum] = [np.array(sets[bnum][cla]) for cla in CLASSES]
    for bnum in range(NUM_KEY_BYTES):
        for cla in CLASSES:
            MEANS_PROFILE[bnum][cla] = np.average(sets[bnum][cla], axis=0)

# Assign to each test trace the trace estimated with the profiling set for the
# same value of the leak variable
def estimate_test():
    global MEANS_TEST
    MEANS_TEST = np.zeros((NUM_KEY_BYTES, len(TRACES_TEST), len(TRACES[0])))
    for bnum in range(NUM_KEY_BYTES):
        for i, trace in enumerate(TRACES_TEST):
            MEANS_TEST[bnum][i] = MEANS_PROFILE[bnum][VARIABLES_TEST[bnum][i]]

# Estimate the Pearson Correlation Coefficient between the test traces and the
# values predicted by the profile (and also compute the p-value)
def estimate_rf_pf(fold):
    global RF, PF
    for bnum in range(NUM_KEY_BYTES):
        for i in range(len(TRACES[0])):
            r,p = pearsonr(TRACES_TEST[:, i], MEANS_TEST[bnum][:, i])
            RF[bnum][fold][i] = r
            PF[bnum][fold][i] = p

# Average the results from k different choices of the test set among the k-folds
def average_folds():
    global RS, PS
    RS = np.average(RF, axis=1)
    PS = np.average(PF, axis=1)

# Compute rz as a measure of the significance of the result
def compute_rzs():
    global RZS
    RZS = 0.5*np.log((1+RS)/(1-RS))
    RZS = RZS * math.sqrt(len(TRACES)-3)
 
# Estimate the k-fold r-test
def estimate_r(k_fold):
    global RS, RZS, PS
    global RF, PF
    # RS = np.zeros((NUM_KEY_BYTES, len(TRACES[0])))
    # RZS = np.zeros((NUM_KEY_BYTES, len(TRACES[0])))
    PS = np.zeros((NUM_KEY_BYTES, len(TRACES[0])))

    RF = np.zeros((NUM_KEY_BYTES, k_fold, len(TRACES[0])))
    PF = np.zeros((NUM_KEY_BYTES, k_fold, len(TRACES[0])))
    for fold in range(0,k_fold):
        split(fold, k_fold)
        classify_and_estimate_profile()
        estimate_test()
        estimate_rf_pf(fold)
    average_folds()
    compute_rzs()

# Compute the Sum of Absolute Differences among classes
def soad():
    global SOADS
    SOADS = np.zeros((NUM_KEY_BYTES, len(TRACES[0])))
    for bnum in range(NUM_KEY_BYTES):    
        for i in CLASSES:
            for j in range(i):
                SOADS[bnum] += np.abs(MEANS[bnum][i] - MEANS[bnum][j])

# Estimate the correlation directly between the variables and the traces
# This makes sense, for example, if the leak follows the Hamming Weight model
# and we chose the Hamming Weight model to compute the variables
def estimate_corr():
    global CORRS, PS
    CORRS = np.zeros((NUM_KEY_BYTES, len(TRACES[0])))
    PS = np.zeros((NUM_KEY_BYTES, len(TRACES[0])))
    for bnum in range(NUM_KEY_BYTES):
        for i in range(len(TRACES[0])):
            CORRS[bnum,i], PS[bnum,i] = pearsonr(TRACES[:, i], VARIABLES[bnum])
        print "byte", bnum, "min: ", np.min(CORRS[bnum]),-np.log10(PS[bnum][np.argmin(CORRS[bnum])])
        print "byte", bnum, "max: ", np.max(CORRS[bnum]),-np.log10(PS[bnum][np.argmax(CORRS[bnum])])

# Given one among r, t, snr, soad, find the Points of Interest by finding the
# peaks
def find_pois(pois_algo, k_fold, num_pois, poi_spacing, template_dir='.'):
    global POIS
    global SNRS, SOADS
    global RZS, RS
    
    RZS = np.zeros((NUM_KEY_BYTES, len(TRACES[0])))
    RS = np.zeros((NUM_KEY_BYTES, len(TRACES[0])))
    POIS = np.zeros((NUM_KEY_BYTES, num_pois), dtype=int)

    informative = np.zeros((NUM_KEY_BYTES, len(TRACES[0])))
    num_plots = 2
    title = ""
    name = ""
    if pois_algo == "soad":
        soad()
        informative = SOADS
        title = "Sum Of Absolute Differences"
        name = "SOAD"
    elif pois_algo == "snr":
        estimate_snr()
        informative = SNRS
        title = "Signal to Noise Ratio: Var_xk(E(traces))/E_xk(Var(traces))"
        name = "SNR"
    elif pois_algo == "t":
        estimate_ttest()
        informative = TTESTS
        title = "t-test"
        name = "T-TEST"
        num_plots = 3
    elif pois_algo == "r":
        estimate_r(k_fold)
        informative = RS
        num_plots = 4
        title = "%d-folded ro-test: r computed with PCC"%k_fold
        name = "r"
    elif pois_algo == "corr":
        estimate_corr()
        informative = CORRS
        title = "Direct correlation between variables and leaks"
        name = "r(L,Y)"
        num_plots = 3
    else:
        raise Exception("POIs algo type %s is not supported" % pois_algo)

    for bnum in range(NUM_KEY_BYTES):
        temp = np.array(informative[bnum])
        for i in range(num_pois):
            poi = np.argmax(temp)
            POIS[bnum][i] = poi
            
            pmin = max(0, poi - poi_spacing)
            pmax = min(poi + poi_spacing, len(temp))
            for j in range(pmin, pmax):
                temp[j] = 0
    
    if PLOT or SAVE_IMAGES:
        plt.subplots_adjust(hspace = 1) 

        plt.subplot(num_plots, 1, 1)
        #plt.title("average trace (%s, %d traces)"%(DATAPATH,len(TRACES)))
        #plt.title("average trace (%d traces)"%(len(TRACES)))
        plt.xlabel("samples")
        plt.ylabel("normalized\namplitude")
        plt.plot(np.average(TRACES, axis=0))
        
        plt.subplot(num_plots, 1, 2)
        #plt.title(title)
        plt.xlabel("samples")
        plt.ylabel(name)
        for i, snr in enumerate(informative):
            plt.plot(snr, label="subkey %d"%i)
        for bnum in range(NUM_KEY_BYTES):
            plt.plot(POIS[bnum], informative[bnum][POIS[bnum]], '*')

        if pois_algo == "r":
            plt.subplot(num_plots, 1, 3)
            plt.title("%d-folded r-test: r_z = 0.5*ln((1+r)/(1-r)) / (1/sqrt(Ntrace-3))"%k_fold)
            plt.xlabel("samples")
            plt.ylabel("r_z")
            for i, rz in enumerate(RZS):
                plt.plot(rz)
            plt.axhline(y=5, label="5", color='green')
            plt.axhline(y=-5, label="-5", color='green')
            plt.legend(loc='upper right')
 
            plt.subplot(num_plots, 1, 4)
            plt.title("%d-folded ro-test: p computed with PCC"%k_fold)
            plt.xlabel("samples")
            plt.ylabel("-log10(p)")
            for i, p in enumerate(PS):
                plt.plot(-np.log10(p))
            plt.axhline(y=-np.log10(0.05), label="0.05", color='orange')
            plt.axhline(y=-np.log10(0.01), label="0.01", color='green')
            plt.legend(loc='upper right')
        
        elif pois_algo == "t":
            plt.subplot(num_plots, 1, 3)
            plt.title("p")
            plt.xlabel("samples")
            plt.ylabel("-log10(p)")
            for i, p in enumerate(PTTESTS):
                plt.plot(-np.log10(p))
            plt.axhline(y=-np.log10(0.05), label="0.05", color='orange')
            plt.axhline(y=-np.log10(0.01), label="0.01", color='green')
            plt.legend(loc='upper right')
        
        elif pois_algo == "corr":
            plt.subplot(num_plots, 1, 3)
            plt.title("p")
            plt.xlabel("samples")
            plt.ylabel("-log10(p)")
            for i, p in enumerate(PS):
                plt.plot(-np.log10(p))
            plt.axhline(y=-np.log10(0.05), label="0.05", color='orange')
            plt.axhline(y=-np.log10(0.01), label="0.01", color='green')
            plt.legend(loc='upper right')
 
        plt.legend()
        if PLOT:
            plt.show()
        if SAVE_IMAGES:
            plt.savefig(os.path.join(template_dir,'pois.pdf'))
            plt.close()

# Once the POIs are known, we can drop all the other points of the traces
# Optionally, instead of taking the peak only, we can take the average of a
# small window areound the peak
def reduce_traces(num_pois, window=0):
    global TRACES_REDUCED
    
    TRACES_REDUCED = np.zeros((NUM_KEY_BYTES, len(TRACES), num_pois))
    for bnum in range(NUM_KEY_BYTES):
        for i, trace in enumerate(TRACES):
            # TRACES_REDUCED[bnum][i] = trace[POIS[bnum,0:num_pois]]
            # find a good reference for the average
            for poi in range(num_pois):
                start = POIS[bnum][poi]-window
                end = POIS[bnum][poi]+window+1   
                TRACES_REDUCED[bnum][i][poi] = np.average(trace[start:end])

# Estimate means, std, and covariance for each possible class
def build_profile(variable, template_dir='.'):
    global PROFILE_MEANS, PROFILE_COVS, PROFILE_STDS

    num_pois = len(POIS[0])
    num_classes = len(CLASSES)

    PROFILE_MEANS = np.zeros((NUM_KEY_BYTES, num_classes, num_pois))
    PROFILE_STDS = np.zeros((NUM_KEY_BYTES, num_classes, num_pois))
    PROFILE_COVS = np.zeros((NUM_KEY_BYTES, num_classes, num_pois, num_pois))

    for bnum in range(NUM_KEY_BYTES):
        for cla in CLASSES:
            for i in range(num_pois):
                PROFILE_MEANS[bnum][cla][i] = MEANS[bnum][cla][POIS[bnum][i]]
                PROFILE_STDS[bnum][cla][i] = STDS[bnum][cla][POIS[bnum][i]]
                for j in range(num_pois):
                    PROFILE_COVS[bnum][cla][i][j] = cov(
                            SETS[bnum][cla][:, POIS[bnum][i]],
                            SETS[bnum][cla][:, POIS[bnum][j]])
  
    if PLOT or SAVE_IMAGES:
        for i in range(num_pois):
            for spine in plt.gca().spines.values():
                    spine.set_visible(False)

            #plt.title("Profiles (%s, %d traces, %s variable, %d classes, poi %d)"%(DATAPATH,
            #    len(TRACES), variable, len(CLASSES), i))
            plt.title("Profile")
            plt.xlabel(variable)
            plt.ylabel("normalized amplitude")
 
            #for bnum in range(0,NUM_KEY_BYTES):
            #    for cla in range(0,256):
            #        plt.errorbar(cla, PROFILE_MEANS[bnum][hw[cla], i],
            #                yerr=PROFILE_STDS[bnum][hw[cla], i],
            #                fmt='--o',
            #                label="subkey %d"%bnum)

            for bnum in range(0,NUM_KEY_BYTES):
                plt.errorbar(CLASSES,
                             PROFILE_MEANS[bnum][:, i],
                             yerr=PROFILE_STDS[bnum][:, i],
                             fmt='--o',
                             label="subkey %d"%bnum)
            plt.legend(loc='upper right')
            if PLOT:
                plt.show()
            if SAVE_IMAGES:
                plt.savefig(os.path.join(template_dir,'profile_poi_%d.pdf'%i),
                        bbox_inches='tight')
                plt.close()

# Find the best (linear) combination of the bits of the leak variable that fits
# the measured traces, compare it with the profile estimated for each possible
# value of the leak variable, and then store it as a profile
def fit(lr_type, variable):
    global PROFILE_BETAS, PROFILE_MEANS_FIT, PROFILE_MEANS
    num_pois = len(POIS[0])

    if lr_type:
        if lr_type == "linear":
            num_betas = 9
            leak_func = lambda x : [(x >> i) & i for i in range(0, num_betas-1)]
        else:
           raise Exception("Linear regression type %s is not supported" %
                    lr_type)
    else:
        return

    PROFILE_BETAS = np.zeros((NUM_KEY_BYTES, num_betas, num_pois))
    for bnum in range(NUM_KEY_BYTES):
        models = list(map(leak_func, VARIABLES[bnum]))
        models = sm.add_constant(models, prepend=False)
        for i in range(num_pois):
            measures = TRACES[:, POIS[bnum][i]]
            params = sm.OLS(measures, models).fit().params
            PROFILE_BETAS[bnum][:, i] = params

    if PLOT:
        for i in range(num_pois):
            for bnum in range(NUM_KEY_BYTES):
                for j in range(0, num_betas - 1):
                    beta = PROFILE_BETAS[bnum][j, i]
                    plt.plot(j, beta, '*')
                    plt.plot([j, j], [0, beta], '-')
            plt.title("Linear regression 8 bits sbox out")
            plt.xlabel("bit")
            plt.ylabel("beta")
            plt.show()

    PROFILE_MEANS_FIT = np.zeros((NUM_KEY_BYTES, len(CLASSES), num_pois))

    for bnum in range(NUM_KEY_BYTES):
        models = list(map(leak_func, CLASSES))
        models = sm.add_constant(models, prepend=False)
        for cla in CLASSES:
            for i in range(num_pois):
                betas = PROFILE_BETAS[bnum][:, i]
                PROFILE_MEANS_FIT[bnum][cla][i] = sum(betas[0:num_betas] *
                        models[cla])
    if PLOT:
        for i in range(num_pois):
            plt.xlabel(variable)
            plt.ylabel("normalized amplitude")
 
            for bnum in range(0,NUM_KEY_BYTES):
                plt.errorbar(CLASSES,
                             PROFILE_MEANS_FIT[bnum][:, i],
                             fmt='--o',
                             label="subkey %d"%bnum)
            plt.legend(loc='upper right')
            plt.show()
 
            plt.xlabel(variable)
            plt.ylabel("normalized amplitude")
            plt.title("profile vs. fit")

            plt.plot(CLASSES,
                         PROFILE_MEANS_FIT[0][:, i],
                         'r-',
                          label="fit")
            plt.errorbar(CLASSES,
                         PROFILE_MEANS[0][:, i],
                         yerr=PROFILE_STDS[bnum][:, i],
                         fmt='g*',
                         label="profile")
            plt.legend(loc='upper right')
            plt.show()

    print ""
    print "Correlation between fit and profile"
    for bnum in range(NUM_KEY_BYTES):
         #print np.corrcoef(PROFILE_MEANS[bnum][:, 0],
         #       PROFILE_MEANS_FIT[bnum][:, 0])[0, 1]
         r,p = pearsonr(PROFILE_MEANS[bnum][:, 0], PROFILE_MEANS_FIT[bnum][:, 0])
         print r, -10*np.log10(p)

    PROFILE_MEANS = PROFILE_MEANS_FIT
    PROFILE_COVS = None
    
# Store useful information about the profile, to be used for comparing profiles,
# or for profiled correlation and template attacks
def save_profile(template_dir):
    np.save(path.join(template_dir, "POIS.npy"), POIS)
    np.save(path.join(template_dir, "PROFILE_RS.npy"), RS)
    np.save(path.join(template_dir, "PROFILE_RZS.npy"), RZS)
    np.save(path.join(template_dir, "PROFILE_MEANS.npy"), PROFILE_MEANS)
    np.save(path.join(template_dir, "PROFILE_STDS.npy"), PROFILE_STDS)
    np.save(path.join(template_dir, "PROFILE_COVS.npy"), PROFILE_COVS)
    np.save(path.join(template_dir, "PROFILE_MEAN_TRACE.npy"),
            PROFILE_MEAN_TRACE)

# Load the profile, for comparison or for attacks
def load_profile(template_dir):
    global PROFILE_MEANS, PROFILE_COVS, POIS, PROFILE_MEAN_TRACE
    global PROFILE_RS, PROFILE_RZS, PROFILE_STDS
    POIS = np.load(path.join(template_dir, "POIS.npy"), POIS)
    PROFILE_RS = np.load(path.join(template_dir, "PROFILE_RS.npy"),
            PROFILE_RS)
    PROFILE_RZS = np.load(path.join(template_dir, "PROFILE_RZS.npy"),
            PROFILE_RZS)
    PROFILE_MEANS = np.load(path.join(template_dir, "PROFILE_MEANS.npy"),
            PROFILE_MEANS)
    PROFILE_COVS = np.load(path.join(template_dir, "PROFILE_COVS.npy"),
            PROFILE_COVS)
    PROFILE_STDS = np.load(path.join(template_dir, "PROFILE_STDS.npy"),
            PROFILE_STDS)
    PROFILE_MEAN_TRACE = np.load(path.join(template_dir,
        "PROFILE_MEAN_TRACE.npy"), PROFILE_MEAN_TRACE)

# Run a template attack or a profiled correlation attack
def run_attack(attack_algo, average_bytes, num_pois, pooled_cov, variable):
    # global PROFILE_MEANS, PROFILE_COVS, POIS
    global LOG_PROBA
 
    LOG_PROBA = [[0 for r in range(256)] for bnum in range(NUM_KEY_BYTES)]

    scores = []
    bestguess = [0]*16
    pge = [256]*16
    
    print ""

    ranking_type = "pearson"
    if attack_algo == "pdf":

        if num_pois > len(PROFILE_COVS[0][0][0]):
            print "Error, there are only %d pois available"%len(PROFILE_COVS[0][0][0])

        for bnum in range(0, NUM_KEY_BYTES):
            if pooled_cov:
                covs = np.average(PROFILE_COVS[bnum,:,0:num_pois,0:num_pois], axis = 0)
            else:
                covs = PROFILE_COVS[bnum][:,0:num_pois,0:num_pois]

            print "Subkey %2d"%bnum
            # Running total of log P_k
            P_k = np.zeros(256)
            for j, trace in enumerate(TRACES):
                P_k_tmp = np.zeros(256)
                # Test each key
                for k in range(256):
                    # Find p_{k,j}
                    if FIXED_PLAINTEXT:
                        cla = VARIABLE_FUNC(k, 0)
                    else:
                        cla = VARIABLE_FUNC(PLAINTEXTS[j][bnum], k)
                    if pooled_cov:
                        cov = covs
                    else:
                        cov = covs[cla]
                    
                    rv = multivariate_normal(PROFILE_MEANS[bnum][cla][0:num_pois], cov)
                    p_kj = rv.pdf(TRACES_REDUCED[bnum][j][0:num_pois])

                    # Add it to running total
                    x = np.log(p_kj)
                    if x == -np.inf:
                        # print "inf"
                        continue
                    P_k_tmp[k] += x
                
                P_k += P_k_tmp

                if j % 100 == 0:
                    print j, "pge ", list(P_k.argsort()[::-1]).index(KEYS[0][bnum])
            LOG_PROBA[bnum] = P_k
            bestguess[bnum] = P_k.argsort()[-1]
            if FIXED_PLAINTEXT:
                pge[bnum] = list(P_k.argsort()[::-1]).index(PLAINTEXTS[0][bnum])
            else:
                pge[bnum] = list(P_k.argsort()[::-1]).index(KEYS[0][bnum])
            print "PGE ", pge[bnum]
            scores.append(P_k)
    
    elif attack_algo == "pcc":
       
        assert len(POIS[0]) >= num_pois, "Requested number of POIs (%d) higher than available (%d)"%(num_pois, len(POIS[0]))

        if average_bytes:
            PROFILE_MEANS_AVG = np.average(PROFILE_MEANS, axis=0)
        for bnum in range(0, NUM_KEY_BYTES):
            cpaoutput = [0]*256
            maxcpa = [0]*256
            print "Subkey %2d"%bnum
            for kguess in range(256):
                
                clas = [VARIABLE_FUNC(PLAINTEXTS[j][bnum], kguess) for j in
                        range(len(TRACES))]
                if average_bytes:
                    leaks = np.asarray([PROFILE_MEANS_AVG[clas[j]] for j in
                        range(len(TRACES))])
                else:
                    leaks = np.asarray([PROFILE_MEANS[bnum][clas[j]] for j in
                        range(len(TRACES))])
                
                # Combine POIs as proposed in 
                # https://pastel.archives-ouvertes.fr/pastel-00850528/document
                maxcpa[kguess] = 1
                for i in range(num_pois):
                    r,p = pearsonr(leaks[:, i], TRACES_REDUCED[bnum][:, i])
                    maxcpa[kguess] *= r

                LOG_PROBA[bnum][kguess] = r
    
            bestguess[bnum] = np.argmax(maxcpa)
    
            cparefs = np.argsort(maxcpa)[::-1]
    
            #Find PGE
            pge[bnum] = list(cparefs).index(KEYS[0][bnum])

    else:
        raise Exception("Attack type not supported: %s"%attack_type)
 
    if FIXED_PLAINTEXT:
        known = PLAINTEXTS[0]
    else:
        known = KEYS[0]

    print_result(bestguess, known, pge)
    return (bestguess == known).all()

# Wrapper to compute AES
def aes(pt, key):
    from Crypto.Cipher import AES
    
    _pt = ''.join([chr(c) for c in pt])
    _key = ''.join([chr(c) for c in key])
    
    cipher = AES.new(_key, AES.MODE_ECB)
    _ct = cipher.encrypt(_pt)
    
    ct = [ord(c) for c in _ct]

    return ct

# Wrapper to call the Histogram Enumeration Library for key-enumeration
def bruteforce(bit_bound_end):
    print ""
    print "Starting key enumeration using HEL"
    import ctypes
    from Crypto.Cipher import AES
 
    from python_hel import hel
   
    pt1 = np.array(PLAINTEXTS[0], dtype=ctypes.c_ubyte)
    pt2 = np.array(PLAINTEXTS[1], dtype=ctypes.c_ubyte)
 
    print "Assuming that we know two plaintext/ciphertext pairs"
    _key = ''.join([chr(c) for c in KEYS[0]])
    _pt1 = ''.join([chr(c) for c in pt1])
    _pt2 = ''.join([chr(c) for c in pt2])
 
    cipher = AES.new(_key, AES.MODE_ECB)
 
    _ct1 = cipher.encrypt(_pt1)
    _ct2 = cipher.encrypt(_pt2)
    
    ct1 = [ord(c) for c in _ct1]
    ct1 = np.array(ct1, dtype=ctypes.c_ubyte)
    ct2 = [ord(c) for c in _ct2]
    ct2 = np.array(ct2, dtype=ctypes.c_ubyte)

    merge = 2
    bins = 512
    bit_bound_start = 0
    #bit_bound_end = 30

    found = hel.bruteforce(LOG_PROBA, pt1, pt2, ct1, ct2, merge,
        bins, bit_bound_start, bit_bound_end)


### CHES20 ATTACKS ###

### Profiled template creation ###
@cli.command()
@click.option("--variable", default="hw_sbox_out", show_default=True,
              help="Variable to attack (hw_sbox_out, hw_p_xor_k, sbox_out, p_xor_k, p, hd)")
@click.option("--lr-type", default=None, show_default=True,
              help="Variable to attack (n_p_xor_k, n_sbox_out)")
@click.option("--pois-algo", default="snr", show_default=True,
              help="Algo used to find pois (snr, soad, r, t)")
@click.option("--k-fold", default=10, show_default=True,
              help="k-fold cross validation.")
@click.option("--num-pois", default=1, show_default=True,
              help="Number of points of interest.")
@click.option("--poi-spacing", default=5, show_default=True,
              help="Minimum number of points between two points of interest.")
@click.option("--pois-dir", default="", type=click.Path(file_okay=False, writable=True),
              help="Reduce the trace using the POIS in this folder")
@click.argument("template_dir", type=click.Path(file_okay=False, writable=True))
def profile(variable, lr_type, pois_algo, k_fold, num_pois, poi_spacing, pois_dir, template_dir):
    """
    Build a template using a chosen technique.

    The template directory is where we store multiple files comprising the
    template; beware that existing files will be overwritten!
    """
    global TRACES

    if pois_dir != "":
        pois = np.load(os.path.join(pois_dir,"POIS.npy"))
        TRACES = TRACES[:,np.sort(pois.flatten())]

    try:
        os.makedirs(template_dir)
    except OSError:
        # Checking the directory before attempting to create it leads to race
        # conditions.
        if not path.isdir(template_dir):
            raise

    compute_variables(variable)
    classify()
    estimate()
    find_pois(pois_algo, k_fold, num_pois, poi_spacing, template_dir)
    build_profile(variable, template_dir)
    fit(lr_type, variable)
    save_profile(template_dir)

### Profiled correlation and template attacks ###
@cli.command()
@click.option("--variable", default="hw_sbox_out", show_default=True,
              help="Variable to attack (hw_sbox_out, hw_p_xor_k, p_xor_k)")
@click.option("--pois-algo", default="", show_default=True,
              help="Algo used to find pois (snr, soad)")
@click.option("--num-pois", default=1, show_default=True,
              help="Number of points of interest.")
@click.option("--poi-spacing", default=5, show_default=True,
              help="Minimum number of points between two points of interest.")
@click.argument("template_dir", type=click.Path(file_okay=False, writable=True))
@click.option("--attack-algo", default="pcc", show_default=True,
              help="Algo used to rank the guesses (pdf, pcc)")
@click.option("--k-fold", default=2, show_default=True,
              help="k-fold cross validation.")
@click.option("--average-bytes/--no-average-bytes", default=False, show_default=True,
              help="Average the profile of the 16 bytes into one, for now it works only with pcc.")
@click.option("--pooled-cov/--no-pooled-cov", default=False, show_default=True,
              help="Pooled covariance for template attacks.")
@click.option("--window", default=0, show_default=True,
              help="Average poi-window to poi+window samples.")
def attack(variable, pois_algo, num_pois, poi_spacing, template_dir,
        attack_algo, k_fold, average_bytes, pooled_cov, window):
    """
    Template attack or profiled correlation attack.

    The template directory is where we store multiple files comprising the
    template.
    """
    
    if not FIXED_KEY and variable != "hw_p" and variable != "p":
        raise Exception("This set DOES NOT use a FIXED KEY")
 
    load_profile(template_dir)
    
    if PLOT:
        plt.plot(POIS[:,0], np.average(TRACES, axis=0)[POIS[:,0]], '*')
        plt.plot(np.average(TRACES, axis=0))
        plt.plot(PROFILE_MEAN_TRACE, 'r')
        plt.show()

    compute_variables(variable)
    
    if num_pois == 0:
        num_pois = len(POIS[0])

    if pois_algo != "":
        classify()
        estimate()
        find_pois(pois_algo, num_pois, k_fold, poi_spacing)

    reduce_traces(num_pois, window)
    found = run_attack(attack_algo, average_bytes, num_pois, pooled_cov,
            variable)

    if BRUTEFORCE and not found:
        bruteforce(BIT_BOUND_END)


### CCS18 ATTACKS, but with new load and new bruteforce ###

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

    if WAIT:
        print("Loading complete")
        raw_input("Press any key to start\n")
 
    if PLOT:
        plt.plot(np.average(TRACES,axis=0),'b')
        plt.show()

    tempKey = KEYS 
    fixed_key = FIXED_KEY 
 
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
    if WAIT:
        print("Loading complete")
        raw_input("Press any key to start")
        
    if PLOT:
        plt.plot(np.average(TRACES,axis=0),'b')
        plt.show()
    
    atkKey = KEYS[0] 
    
    scores = []
    bestguess = [0]*16
    pge = [256]*16

    tot = 0
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

            guessed = P_k.argsort()[-1]
            window[window_index] = guessed
            window_index = (window_index + 1) % len(window)
            if j % 10 == 1:
                # import os
                # os.system('clear')
                print "PGE ",list(P_k.argsort()[::-1]).index(atkKey[knum]),
                # for g in P_k.argsort()[::-1]:
                    # if g == atkKey[knum]:
                        # print '\033[92m%02x\033[0m'%g,
                    # else:
                        # print '%02x'%g,
                print ""
            
            if all(k == atkKey[knum] for k in window) or (j == len(TRACES)-1 and guessed == atkKey[knum]):
                print "subkey %2d found with %4d traces" % (knum, j)
                tot += 1
                break
        else:
            p = list(P_k.argsort()[::-1]).index(atkKey[knum])
            print "subkey %2d NOT found, PGE = %3d" %(knum,p)

        print ""
        bestguess[knum] = P_k.argsort()[-1]
        pge[knum] = list(P_k.argsort()[::-1]).index(atkKey[knum])
        scores.append(P_k)
   
    print_result(bestguess, atkKey, pge)
    # if BRUTEFORCE:
        # brute_force_bitflip(bestguess, atkKey)
    if BRUTEFORCE and not (bestguess == KEYS[0]).all():
        bruteforce(BIT_BOUND_END)

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
    global LOG_PROBA
    LOG_PROBA = [[0 for r in range(256)] for bnum in range(NUM_KEY_BYTES)]
    
    if WAIT:
        print("Loading complete")
        raw_input("Press any key to start")
 
    if PLOT:
        for t in TRACES:
            plt.plot(t,linewidth=0.5)
        avg = np.average(TRACES, axis=0)
        plt.plot(avg, 'b', linewidth=2, label="average")
        # np.save("tpl_template.npy",avg)
        plt.xlabel("samples")
        plt.ylabel("normalized\namplitude")
        plt.legend()
        plt.show()

        # 4: Find sum of differences
        tempSumDiff = np.zeros(np.shape(TRACES)[1])
        for i in range(np.shape(TRACES)[0]-1-5):
            for j in range(i, i+5):
                tempSumDiff += np.abs(TRACES[i] - TRACES[j])
        plt.plot(tempSumDiff)
        plt.show()
    
    knownkey = KEYS[0] 
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
            LOG_PROBA[bnum][kguess] = maxcpa[kguess]
            print maxcpa[kguess]
    
        bestguess[bnum] = np.argmax(maxcpa)
    
        cparefs = np.argsort(maxcpa)[::-1]
    
        #Find PGE
        pge[bnum] = list(cparefs).index(knownkey[bnum])
        stored_cpas.append(maxcpa)
    
    print_result(bestguess, knownkey, pge)
    # if BRUTEFORCE:
        # brute_force(stored_cpas, knownkey)
    if BRUTEFORCE and not (bestguess == KEYS[0]).all():
        bruteforce(BIT_BOUND_END)

if __name__ == "__main__":
    cli()
