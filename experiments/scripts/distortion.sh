#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
cd $SC/experiments

# git checkout ches20

### Profile conventional, Figure 5a and 5b
sc-attack --num-key-bytes 1 --plot --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_template/ --start-point 1000 --end-point 2000 --num-traces 5000 profile --num-pois 1 --poi-spacing 1 --variable hw_sbox_out --pois-algo r /tmp/distortion/conventional/hw_sbox_out
sc-attack --num-key-bytes 1 --plot --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_template/ --start-point 1000 --end-point 2000 --num-traces 5000 profile --num-pois 1 --poi-spacing 1 --variable p_xor_k --pois-algo r /tmp/distortion/conventional/p_xor_k

python src/screamingchannels/sc-compare.py --plot --align --num-key-bytes 1 /tmp/distortion/conventional/p_xor_k/ /tmp/distortion/conventional/hw_sbox_out/ compare

### Direct correlation
sc-attack --num-key-bytes 1 --plot --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_template/ --start-point 1000 --end-point 2000 --num-traces 5000 profile --num-pois 1 --poi-spacing 1 --variable hw_sbox_out --pois-algo corr /tmp/distortion/conventional/hw_sbox_out_corr

### Profile also cable and 10cm
sc-attack --num-key-bytes 1 --plot --norm --data-path $TRACES_CHES20/ches20/hackrf_cable/ro_test_template/ --start-point 900 --end-point 1500 --num-traces 5000 profile --variable hw_sbox_out --pois-algo r --num-pois 1 /tmp/distortion/cable/hw_sbox_out
sc-attack --num-key-bytes 1 --plot --norm --data-path $TRACES_CHES20/ches20/hackrf_cable/ro_test_template/ --start-point 900 --end-point 1500 --num-traces 5000 profile --variable p_xor_k --pois-algo r --num-pois 1 /tmp/distortion/cable/p_xor_k
sc-attack --num-key-bytes 1 --plot --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/template_tx_500/ --start-point 0 --end-point 0 --num-traces 5000 profile --variable hw_sbox_out --pois-algo r --num-pois 1 /tmp/distortion/10cm/hw_sbox_out
sc-attack --num-key-bytes 1 --plot --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/template_tx_500/ --start-point 0 --end-point 0 --num-traces 5000 profile --variable p_xor_k --pois-algo r --num-pois 1 /tmp/distortion/10cm/p_xor_k

### Correlation between conventional,cable, and 10cm
python src/screamingchannels/sc-compare.py --align --num-key-bytes 1 /tmp/distortion/conventional/p_xor_k/ /tmp/distortion/cable/p_xor_k/ compare 
python src/screamingchannels/sc-compare.py --align --num-key-bytes 1 /tmp/distortion/conventional/p_xor_k/ /tmp/distortion/10cm/p_xor_k/ compare
python src/screamingchannels/sc-compare.py --align --num-key-bytes 1 /tmp/distortion/cable/p_xor_k/ /tmp/distortion/10cm/p_xor_k/ compare

### Figure 6a, 6b
python src/screamingchannels/sc-compare.py --plot --align --num-key-bytes 1 /tmp/distortion/cable/p_xor_k/ /tmp/distortion/cable/hw_sbox_out/ compare
python src/screamingchannels/sc-compare.py --plot --align --num-key-bytes 1 /tmp/distortion/10cm/p_xor_k/ /tmp/distortion/10cm/hw_sbox_out/ compare

### Figure 6c, 6d
python src/screamingchannels/sc-compare.py --plot --align --num-key-bytes 1 /tmp/distortion/cable/hw_sbox_out/ /tmp/distortion/10cm/hw_sbox_out/ compare
python src/screamingchannels/sc-compare.py --plot --align --num-key-bytes 1 /tmp/distortion/cable/p_xor_k/ /tmp/distortion/10cm/p_xor_k/ compare

### Profile all bytes
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_template/ --start-point 1100 --end-point 1700 --num-traces 5000 profile --num-pois 1 --poi-spacing 1 --variable p_xor_k --pois-algo r /tmp/distortion/conventional/r/p_xor_k
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_template/ --start-point 1100 --end-point 1700 --num-traces 5000 profile --num-pois 1 --poi-spacing 1 --variable hw_sbox_out --pois-algo r /tmp/distortion/conventional/r/hw_sbox_out
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/template_tx_500/ --start-point 0 --end-point 0 --num-traces 5000 profile --variable p_xor_k --pois-algo r --num-pois 1 /tmp/distortion/10cm/r/p_xor_k
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/template_tx_500/ --start-point 0 --end-point 0 --num-traces 5000 profile --variable hw_sbox_out --pois-algo r --num-pois 1 /tmp/distortion/10cm/r/hw_sbox_out


### Table2 attacks
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_attack/ --start-point 1100 --end-point 1700 --num-traces 14 --bruteforce attack --num-pois 1 --variable hw_sbox_out /tmp/distortion/conventional/r/hw_sbox_out --attack-algo pdf --pooled-cov
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_attack/ --start-point 1100 --end-point 1700 --num-traces 14 --bruteforce attack --num-pois 1 --variable hw_sbox_out /tmp/distortion/conventional/r/hw_sbox_out
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_attack/ --start-point 1100 --end-point 1700 --num-traces 14 --bruteforce attack --num-pois 1 --variable p_xor_k /tmp/distortion/conventional/r/p_xor_k
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_attack/ --start-point 1100 --end-point 1700 --num-traces 14 --bruteforce attack --num-pois 1 --variable p_xor_k /tmp/distortion/conventional/r/p_xor_k --attack-algo pdf --pooled-cov
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/attack_tx_500/ --start-point 0 --end-point 0 --num-traces 1273 --bruteforce --bit-bound-end 27 attack --variable hw_sbox_out --num-pois 1 /tmp/distortion/10cm/r/hw_sbox_out --attack-algo pdf --pooled-cov
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/attack_tx_500/ --start-point 0 --end-point 0 --num-traces 1273 --bruteforce --bit-bound-end 27 attack --variable hw_sbox_out --num-pois 1 /tmp/distortion/10cm/r/hw_sbox_out
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/attack_tx_500/ --start-point 0 --end-point 0 --num-traces 1273 --bruteforce attack --variable p_xor_k --num-pois 1 /tmp/distortion/10cm/r/p_xor_k --attack-algo pdf --pooled-cov
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/attack_tx_500/ --start-point 0 --end-point 0 --num-traces 1273 --bruteforce attack --variable p_xor_k --num-pois 1 /tmp/distortion/10cm/r/p_xor_k 

python << END
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import multivariate_normal, linregress, norm, pearsonr, entropy
from os import path
from tabulate import tabulate

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

def load_profile(dir):
    POIS = np.load(path.join(dir, "POIS.npy"))
    RS = np.load(path.join(dir, "PROFILE_RS.npy"))
    RZS = np.load(path.join(dir, "PROFILE_RZS.npy"))
    MEANS = np.load(path.join(dir, "PROFILE_MEANS.npy"))
    STDS = np.load(path.join(dir, "PROFILE_STDS.npy"))
    COVS = np.load(path.join(dir, "PROFILE_COVS.npy"))
    MEAN_TRACE = np.load(path.join(dir, "PROFILE_MEAN_TRACE.npy"))
    return RS, RZS

dirs = [
    "/tmp/distortion/conventional/r/hw_sbox_out",
    "/tmp/distortion/conventional/r/p_xor_k",
    "/tmp/distortion/10cm/r/hw_sbox_out",
    "/tmp/distortion/10cm/r/p_xor_k",
]
for dir in dirs:
    r, rz = load_profile("%s"%dir)
    rmax = np.max(r)
    amx = np.unravel_index(r.argmax(), r.shape)
    rzmax = rz[amx]
    print dir, rmax, rzmax
    #print "%s $%.2f$, $%3.0f$"%(dir, rmax, rzmax)
END

### study distortion with linear regression

# conventional Figure 7a and correlation
sc-attack --num-key-bytes 1 --plot --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_template/ --start-point 1000 --end-point 2000 --num-traces 5000 profile --num-pois 1 --poi-spacing 1 --variable sbox_out --lr-type linear --pois-algo r /tmp/distortion/conventional/n_sbox_out
# screaming Figure 7b and correlation
sc-attack --plot --num-key-bytes 1 --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/template_tx_500/ --start-point 0 --end-point 0 --num-traces 5000 profile --variable sbox_out --lr-type linear --pois-algo r --num-pois 1 /tmp/distortion/10cm/r/n_sbox_out
